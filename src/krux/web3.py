# The MIT License (MIT)
#
# Copyright (c) 2021-2024 Krux contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import io
import hashlib
import math
from binascii import a2b_base64, crc32, hexlify, unhexlify

try:
    import zlib
except ImportError:
    zlib = None

try:
    import ujson as json
except ImportError:
    import json

try:
    from typing import Any, Dict, List, Optional, Sequence, Tuple
except ImportError:
    # MaixPy/MicroPython does not ship typing; these names only support
    # desktop annotation evaluation and are ignored by the firmware compiler.
    class _TypeAlias:
        def __getitem__(self, _item):
            return self

    Any = Dict = List = Optional = Sequence = Tuple = _TypeAlias()

from embit import bip32, ec, hashes
from embit.util import secp256k1
from ur.ur import UR
from ur.ur_decoder import URDecoder
from ur.ur_encoder import UREncoder
from urtypes.cbor import DataItem, Decoder as CborDecoder, Encoder as CborEncoder
from urtypes.crypto import CoinInfo, HDKey, Keypath, PathComponent

DEFAULT_EVM_ACCOUNT_PATH = "m/44'/60'/0'"
DEFAULT_EVM_ADDRESS_PATH = "m/44'/60'/0'/0/0"
DEFAULT_EVM_CHILDREN_PATH = "0/*"
WEB3_ETH_COIN_TYPE = 0x3C
WEB3_BTC_COIN_TYPE = 0
WEB3_MAINNET_NETWORK = 0
WEB3_WALLET_PROFILE_OKX = "okx"
WEB3_WALLET_PROFILE_BITGET = "bitget"
WEB3_WALLET_PROFILE_METAMASK = "metamask"
WEB3_WALLET_PROFILE_RABBY = "rabby"
WEB3_WALLET_PROFILE_TOKENPOCKET = "tokenpocket"
WEB3_WALLET_PROFILE_LABELS = {
    WEB3_WALLET_PROFILE_OKX: "OKX 钱包",
    WEB3_WALLET_PROFILE_BITGET: "Bitget 钱包",
    WEB3_WALLET_PROFILE_METAMASK: "MetaMask",
    WEB3_WALLET_PROFILE_RABBY: "Rabby",
    WEB3_WALLET_PROFILE_TOKENPOCKET: "TokenPocket",
}
WEB3_OKX_DEVICE_TYPE = "Keystone 3 Pro"
WEB3_KEYSTONE_DEVICE_TYPE = "Keystone 3 Pro"
WEB3_KEYSTONE_DEVICE_VERSION = "1.0.4"
WEB3_OKX_LEDGER_LIVE_ACCOUNT_COUNT = 10
WEB3_OKX_BTC_ACCOUNT_PATHS = ("m/49'/0'/0'", "m/84'/0'/0'")
WEB3_BITGET_BTC_ACCOUNT_PATHS = ("m/84'/0'/0'",)
WEB3_OKX_CONNECT_QR_MAX_FRAGMENT_LEN = 160
RELAY_TP_PREFIX = "tpr1:"
RELAY_WEB3_PREFIX = "w3r1:"

TRANSACTION_ACTIONS = {"signtransaction", "sendtransaction", "ethsendtransaction"}
PERSONAL_ACTIONS = {"personalsign", "signpersonalmessage", "ethsign", "signmessage"}
TYPED_DATA_ACTIONS = {
    "signtypeddata",
    "signtypeddatav4",
    "signtypedatav4",
    "signtypeddatalegacy",
    "signtypedata",
    "ethsigntypeddata",
    "ethsigntypeddatav4",
    "ethsigntypedatav4",
}


def _crc32_text(text):
    return str(crc32(text.encode("utf-8")) & 0xFFFFFFFF)


def _sha256(data):
    return hashlib.sha256(data).digest()


def _bytes_hex(data):
    """Return lowercase hex text with MaixPy-compatible binascii."""
    return hexlify(bytes(data)).decode("ascii")


def _bytes_from_hex(text):
    """Decode hex text with MaixPy-compatible binascii."""
    return bytes(unhexlify(text))


def _sha256_hex(data):
    return _bytes_hex(_sha256(data))


def _json_dumps_compact(data):
    """Dump JSON with CPython options, falling back for MicroPython ujson."""
    try:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return json.dumps(data)


def _deflateio_decompress(compressed, fmt=None, wbits=15):
    try:
        import deflate
    except ImportError:
        raise Web3Error("当前固件不支持中转二维码解压")

    formats = []
    if fmt is not None:
        formats.append(fmt)
    else:
        formats.append(getattr(deflate, "AUTO", 0))
        formats.append(getattr(deflate, "RAW", 1))
        formats.append(None)

    last_error = None
    for candidate in formats:
        stream = io.BytesIO(compressed)
        try:
            if candidate is None:
                reader = deflate.DeflateIO(stream)
            else:
                try:
                    reader = deflate.DeflateIO(stream, candidate, wbits)
                except TypeError:
                    reader = deflate.DeflateIO(stream, candidate)
        except Exception as exc:
            last_error = exc
            continue

        chunks = []
        try:
            while True:
                chunk = reader.read(256)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        except Exception as exc:
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise Web3Error("当前固件不支持中转二维码解压")


def _deflate_format(name, fallback):
    try:
        import deflate

        return getattr(deflate, name, fallback)
    except ImportError:
        return fallback


def _deflateio_decompress_auto(compressed):
    return _deflateio_decompress(
        compressed,
        _deflate_format("AUTO", 0),
        wbits=15,
    )


def _deflateio_decompress_raw(compressed):
    return _deflateio_decompress(
        compressed,
        _deflate_format("RAW", 1),
        wbits=15,
    )


def _deflateio_decompress_zlib(compressed):
    return _deflateio_decompress(
        compressed,
        _deflate_format("ZLIB", 2),
        wbits=15,
    )


def _deflateio_decompress_gzip(compressed):
    return _deflateio_decompress(
        compressed,
        _deflate_format("GZIP", 3),
        wbits=15,
    )


def _deflateio_decompress_legacy_raw(compressed):
    try:
        import deflate
    except ImportError:
        raise Web3Error("当前固件不支持中转二维码解压")

    reader = deflate.DeflateIO(io.BytesIO(compressed))
    chunks = []
    while True:
        chunk = reader.read(256)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _raw_deflate_decompress(compressed):
    if zlib is not None and hasattr(zlib, "decompress"):
        return zlib.decompress(compressed, -15)
    try:
        return _deflateio_decompress_raw(compressed)
    except Exception:
        return _deflateio_decompress_legacy_raw(compressed)


def _zlib_decompress(compressed, raw=False):
    if raw:
        return _raw_deflate_decompress(compressed)

    if zlib is not None and hasattr(zlib, "decompress"):
        return zlib.decompress(compressed)

    if len(compressed) > 6:
        cmf = compressed[0]
        flg = compressed[1]
        if (cmf & 0x0F) == 8 and ((cmf << 8) + flg) % 31 == 0:
            try:
                return _deflateio_decompress_zlib(compressed)
            except Exception:
                return _raw_deflate_decompress(compressed[2:-4])

    if zlib is not None and hasattr(zlib, "DeflateIO"):
        fmt = zlib.ZLIB
        reader = zlib.DeflateIO(io.BytesIO(compressed), fmt)
        chunks = []
        while True:
            chunk = reader.read(256)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)

    raise Web3Error("当前固件不支持中转二维码解压")


def _gzip_decompress_with_zlib(compressed):
    if zlib is not None and hasattr(zlib, "decompress"):
        return zlib.decompress(compressed, 16 + 15)
    try:
        return _deflateio_decompress_gzip(compressed)
    except Exception:
        return _gzip_decompress(compressed)


class Web3Error(ValueError):
    """Raised for malformed or unsupported Web3 payloads."""


def _web3_request_type_label(data_type):
    if data_type == Web3RequestDataType.TRANSACTION:
        return "交易签名"
    if data_type == Web3RequestDataType.TYPED_DATA:
        return "结构化数据签名"
    if data_type == Web3RequestDataType.PERSONAL_MESSAGE:
        return "消息签名"
    return "结构化交易签名"


class _Web3RequestDataTypeValue(int):
    def label(self):
        return _web3_request_type_label(self)


class Web3RequestDataType:
    TRANSACTION = _Web3RequestDataTypeValue(1)
    TYPED_DATA = _Web3RequestDataTypeValue(2)
    PERSONAL_MESSAGE = _Web3RequestDataTypeValue(3)
    TYPED_TRANSACTION = _Web3RequestDataTypeValue(4)

    @classmethod
    def from_code(cls, code):
        if code == cls.TRANSACTION:
            return cls.TRANSACTION
        if code == cls.TYPED_DATA:
            return cls.TYPED_DATA
        if code == cls.PERSONAL_MESSAGE:
            return cls.PERSONAL_MESSAGE
        if code == cls.TYPED_TRANSACTION:
            return cls.TYPED_TRANSACTION
        raise Web3Error("暂不支持的链上请求类型: {}".format(code))

class TpParsedRequest:
    def __init__(
        self,
        raw_payload,
        namespace,
        action,
        request_format,
        version,
        protocol,
        network,
        chain_id,
        request_id,
        action_id,
        data_id,
        dapp_name,
        dapp_url,
        dapp_source,
        address,
        kind,
        message,
        typed_data_json,
        tx_data,
    ):
        self.raw_payload = raw_payload
        self.namespace = namespace
        self.action = action
        self.request_format = request_format
        self.version = version
        self.protocol = protocol
        self.network = network
        self.chain_id = chain_id
        self.request_id = request_id
        self.action_id = action_id
        self.data_id = data_id
        self.dapp_name = dapp_name
        self.dapp_url = dapp_url
        self.dapp_source = dapp_source
        self.address = address
        self.kind = kind
        self.message = message
        self.typed_data_json = typed_data_json
        self.tx_data = tx_data


class Web3Request:
    def __init__(
        self,
        source_format,
        data_type,
        chain_id,
        derivation_path,
        address,
        origin,
        request_id_value,
        request_id_text,
        sign_data,
        raw_payload,
        message_text=None,
        typed_data_json=None,
        tp_request=None,
        relay_wallet_name=None,
        relay_format=None,
        relay_qr_type=None,
        relay_chain_hint=None,
    ):
        self.source_format = source_format
        self.data_type = data_type
        self.chain_id = chain_id
        self.derivation_path = derivation_path
        self.address = address
        self.origin = origin
        self.request_id_value = request_id_value
        self.request_id_text = request_id_text
        self.sign_data = sign_data
        self.raw_payload = raw_payload
        self.message_text = message_text
        self.typed_data_json = typed_data_json
        self.tp_request = tp_request
        self.relay_wallet_name = relay_wallet_name
        self.relay_format = relay_format
        self.relay_qr_type = relay_qr_type
        self.relay_chain_hint = relay_chain_hint


class Web3QrBundle:
    def __init__(self, ur, pages, text=None):
        self.ur = ur
        self.pages = pages
        self.text = text


class Web3AccountInfo:
    def __init__(
        self,
        account_path,
        address_path,
        children_path,
        address,
        display_address,
        master_fingerprint,
        master_fingerprint_hex,
        compressed_pubkey_hex,
        chain_code_hex,
        xpub,
        origin_keypath,
        children_keypath,
    ):
        self.account_path = account_path
        self.address_path = address_path
        self.children_path = children_path
        self.address = address
        self.display_address = display_address
        self.master_fingerprint = master_fingerprint
        self.master_fingerprint_hex = master_fingerprint_hex
        self.compressed_pubkey_hex = compressed_pubkey_hex
        self.chain_code_hex = chain_code_hex
        self.xpub = xpub
        self.origin_keypath = origin_keypath
        self.children_keypath = children_keypath


class Web3SigningResult:
    def __init__(
        self,
        request,
        signer_address,
        digest,
        signature_bytes,
        signature_hex,
        qr_bundle,
    ):
        self.request = request
        self.signer_address = signer_address
        self.digest = digest
        self.signature_bytes = signature_bytes
        self.signature_hex = signature_hex
        self.qr_bundle = qr_bundle


class EvmAccessListEntry:
    def __init__(self, address, storage_keys):
        self.address = address
        self.storage_keys = storage_keys


class EvmUnsignedTransaction:
    def __init__(
        self,
        tx_type,
        chain_id,
        nonce,
        gas_limit,
        to,
        value,
        data,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        access_list=None,
    ):
        self.tx_type = tx_type
        self.chain_id = chain_id
        self.nonce = nonce
        self.gas_limit = gas_limit
        self.to = to
        self.value = value
        self.data = data
        self.gas_price = gas_price
        self.max_priority_fee_per_gas = max_priority_fee_per_gas
        self.max_fee_per_gas = max_fee_per_gas
        self.access_list = access_list if access_list is not None else []


class TpMultiFragment:
    def __init__(self, index, total, chunk, crc32):
        self.index = index
        self.total = total
        self.chunk = chunk
        self.crc32 = crc32


class RelayFragment:
    def __init__(self, prefix, index, total, chunk, crc32):
        self.prefix = prefix
        self.index = index
        self.total = total
        self.chunk = chunk
        self.crc32 = crc32


class Web3RelayEnvelope:
    def __init__(
        self,
        wallet,
        wallet_name,
        detected_format,
        qr_type,
        action,
        chain,
        payload,
        response_protocol=None,
        request_id=None,
        origin=None,
        data_type_name=None,
        request_data_type_id=None,
        request_sign_data_hex=None,
        chain_id=None,
        address=None,
        address_path=None,
        expected_address=None,
    ):
        self.wallet = wallet
        self.wallet_name = wallet_name
        self.detected_format = detected_format
        self.qr_type = qr_type
        self.action = action
        self.chain = chain
        self.payload = payload
        self.response_protocol = response_protocol
        self.request_id = request_id
        self.origin = origin
        self.data_type_name = data_type_name
        self.request_data_type_id = request_data_type_id
        self.request_sign_data_hex = request_sign_data_hex
        self.chain_id = chain_id
        self.address = address
        self.address_path = address_path
        self.expected_address = expected_address


class TpMultiFragmentAssembler:
    def __init__(self) -> None:
        self.expected_total = None
        self.expected_crc = None
        self.raw_fragments = {}

    def reset(self) -> None:
        self.expected_total = None
        self.expected_crc = None
        self.raw_fragments.clear()

    @property
    def received_count(self) -> int:
        return len(self.raw_fragments)

    def accept(self, fragment: TpMultiFragment) -> Tuple[str, Optional[str]]:
        total = fragment.total
        index = fragment.index
        if total <= 0:
            return "error", "分片总数不合法"

        valid_one_based = 1 <= index <= total
        valid_zero_based = 0 <= index < total
        if not valid_one_based and not valid_zero_based:
            return "error", "分片索引不合法 (index={} total={})".format(index, total)

        if self.expected_total is None:
            self.expected_total = total
            self.expected_crc = fragment.crc32
        elif self.expected_total != total or self.expected_crc != fragment.crc32:
            self.reset()
            return "error", "分片属于不同二维码序列，已重置"

        self.raw_fragments[index] = fragment.chunk

        expected = self.expected_total or total
        if self.received_count < expected:
            return "progress", "已接收分片 {}/{}".format(self.received_count, expected)

        payload = self._assemble_payload(expected)
        if payload is None:
            self.reset()
            return "error", "分片索引基准不一致或有缺片"

        crc = _crc32_text(payload)
        if crc != self.expected_crc:
            self.reset()
            return "error", "分片 CRC 校验失败"

        self.reset()
        return "complete", payload

    def _assemble_payload(self, total: int) -> Optional[str]:
        if all(i in self.raw_fragments for i in range(1, total + 1)):
            return "".join(self.raw_fragments[i] for i in range(1, total + 1))
        if all(i in self.raw_fragments for i in range(0, total)):
            return "".join(self.raw_fragments[i] for i in range(0, total))
        return None


class RelayFragmentAssembler:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.lower()
        self.expected_total = None
        self.expected_crc = None
        self.raw_fragments = {}

    def reset(self) -> None:
        self.expected_total = None
        self.expected_crc = None
        self.raw_fragments.clear()

    @property
    def received_count(self) -> int:
        return len(self.raw_fragments)

    def accept(self, fragment: RelayFragment) -> Tuple[str, Optional[str]]:
        if fragment.prefix.lower() != self.prefix:
            self.reset()
            return "error", "分片前缀不一致"

        total = fragment.total
        index = fragment.index
        if total <= 0:
            return "error", "分片总数不合法"
        if not (1 <= index <= total):
            return "error", "分片索引不合法 (index={} total={})".format(index, total)

        if self.expected_total is None:
            self.expected_total = total
            self.expected_crc = fragment.crc32
        elif self.expected_total != total or self.expected_crc != fragment.crc32:
            self.reset()
            return "error", "分片属于不同二维码序列，已重置"

        self.raw_fragments[index] = fragment.chunk

        expected = self.expected_total or total
        if self.received_count < expected:
            return "progress", "已接收分片 {}/{}".format(self.received_count, expected)

        encoded = self._assemble_payload(expected)
        if encoded is None:
            self.reset()
            return "error", "分片索引基准不一致或有缺片"

        crc = _crc32_text(encoded)
        if crc != self.expected_crc:
            self.reset()
            return "error", "分片 CRC 校验失败"

        self.reset()
        return "complete", encoded

    def _assemble_payload(self, total: int) -> Optional[str]:
        if all(i in self.raw_fragments for i in range(1, total + 1)):
            return "".join(self.raw_fragments[i] for i in range(1, total + 1))
        return None


# -----------------------------
# Hex / string / address helpers
# -----------------------------


def _starts_with_any(value: str, prefixes: Sequence[str]) -> bool:
    """MicroPython-compatible replacement for str.startswith(tuple)."""
    for prefix in prefixes:
        if value.startswith(prefix):
            return True
    return False


def _ends_with_any(value: str, suffixes: Sequence[str]) -> bool:
    """MicroPython-compatible replacement for str.endswith(tuple)."""
    for suffix in suffixes:
        if value.endswith(suffix):
            return True
    return False


def _clean_hex_prefix(value: str) -> str:
    if _starts_with_any(value, ("0x", "0X")):
        return value[2:]
    return value


def _ensure_hex_prefix(value: str) -> str:
    if _starts_with_any(value, ("0x", "0X")):
        return value
    return "0x{}".format(value)


def _hex_to_bytes(value: Optional[str]) -> bytes:
    if value is None:
        return b""
    text = _clean_hex_prefix(value.strip())
    if not text:
        return b""
    if len(text) % 2:
        text = "0" + text
    try:
        return _bytes_from_hex(text)
    except Exception as exc:
        raise Web3Error("Invalid hex string") from exc


def bytes_to_hex(data: bytes) -> str:
    return _bytes_hex(data)


def normalize_eth_address(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    text = _ensure_hex_prefix(_clean_hex_prefix(text)).lower()
    if len(_clean_hex_prefix(text)) != 40:
        raise Web3Error("地址格式无效: {}".format(value))
    return text


def _shorten_middle(value: str, prefix_len: int = 10, suffix_len: int = 8) -> str:
    if len(value) <= prefix_len + suffix_len + 3:
        return value
    return "{}...{}".format(value[:prefix_len], value[-suffix_len:])


def ethereum_checksum_address(value: str) -> str:
    normalized = normalize_eth_address(value)
    if normalized is None:
        raise Web3Error("地址为空")
    clean = _clean_hex_prefix(normalized)
    digest = _bytes_hex(keccak256(clean.encode("ascii")))
    result = ["0x"]
    for index, char in enumerate(clean):
        if char.isdigit():
            result.append(char)
        else:
            result.append(char.upper() if int(digest[index], 16) >= 8 else char)
    return "".join(result)


def ethereum_address_from_bytes(address_bytes: bytes) -> str:
    if len(address_bytes) != 20:
        raise Web3Error("地址长度不正确")
    return _ensure_hex_prefix(_bytes_hex(address_bytes))


def ethereum_address_from_pubkey(pubkey_uncompressed: bytes) -> str:
    if len(pubkey_uncompressed) != 65 or pubkey_uncompressed[0] != 0x04:
        raise Web3Error("Expected uncompressed 65-byte public key")
    return _ensure_hex_prefix(_bytes_hex(keccak256(pubkey_uncompressed[1:])[-20:]))


def public_key_to_uncompressed_bytes(pubkey: ec.PublicKey) -> bytes:
    return ec.PublicKey(pubkey._point, compressed=False).sec()  # pylint: disable=protected-access


def decode_personal_message(message: str | bytes) -> bytes:
    if isinstance(message, (bytes, bytearray)):
        return bytes(message)
    if _starts_with_any(message, ("0x", "0X")):
        try:
            return _hex_to_bytes(message)
        except Exception:
            return message.encode("utf-8")
    return message.encode("utf-8")


def _maybe_text(value: bytes) -> Optional[str]:
    try:
        text = value.decode("utf-8")
    except Exception:
        return None
    if not text.strip():
        return None
    if any(ord(char) < 32 and char not in "\r\n\t" for char in text):
        return None
    return text


def _parse_request_id_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (bytes, bytearray)):
        text = _maybe_text(bytes(value))
        if text is not None:
            return text
        return _bytes_hex(value)
    if isinstance(value, DataItem):
        return _parse_request_id_text(value.map if hasattr(value, "map") else value)
    return str(value)


def _extract_path_from_keypath(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, Keypath):
        path = value.path()
        if not path:
            return None
        return "m/{}".format(path)
    if isinstance(value, DataItem):
        return _extract_path_from_keypath(Keypath.from_data_item(value))
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _normalize_path(path: Optional[str], default: str = DEFAULT_EVM_ADDRESS_PATH) -> str:
    if path is None:
        return default
    text = path.strip()
    if not text:
        return default
    if not text.startswith("m"):
        text = "m/{}".format(text.lstrip("/"))
    return text


def _parse_path_components(path: str, allow_wildcard: bool = False) -> List[PathComponent]:
    trimmed = path.strip()
    if not trimmed or trimmed == "m":
        return []
    if trimmed.startswith("m/"):
        trimmed = trimmed[2:]
    elif trimmed.startswith("m"):
        trimmed = trimmed[1:].lstrip("/")
    parts = [part for part in trimmed.split("/") if part]
    components = []
    for part in parts:
        if allow_wildcard and part == "*":
            components.append(PathComponent(None, False))
            continue
        hardened = _ends_with_any(part, ("'", "h", "H"))
        numeric = part[:-1] if hardened else part
        if not numeric.isdigit():
            raise Web3Error("派生路径片段无效: {}".format(part))
        components.append(PathComponent(int(numeric), hardened))
    return components


def _keypath(path: str, source_fingerprint: Optional[bytes] = None, depth: Optional[int] = None) -> Keypath:
    return Keypath(_parse_path_components(path), source_fingerprint, depth)


def _keypath_from_components(
    path: str, source_fingerprint: Optional[bytes] = None, depth: Optional[int] = None, allow_wildcard: bool = False
) -> Keypath:
    return Keypath(_parse_path_components(path, allow_wildcard=allow_wildcard), source_fingerprint, depth)


def _encode_cbor(item: Any) -> bytes:
    out = io.BytesIO()
    encoder = CborEncoder(out)
    encoder.encode(item)
    return out.getvalue()


def _decode_cbor_map(cbor_bytes: bytes) -> Dict[Any, Any]:
    item = CborDecoder(io.BytesIO(cbor_bytes)).decode()
    if not isinstance(item, dict):
        raise Web3Error("CBOR 不是对象")
    return item


# -----------------------------
# Keccak-256
# -----------------------------


KECCAK_ROTATIONS = [
    0,
    1,
    62,
    28,
    27,
    36,
    44,
    6,
    55,
    20,
    3,
    10,
    43,
    25,
    39,
    41,
    45,
    15,
    21,
    8,
    18,
    2,
    61,
    56,
    14,
]
KECCAK_PERMUTATION = [
    1,
    6,
    9,
    22,
    14,
    20,
    2,
    12,
    13,
    19,
    23,
    15,
    4,
    24,
    21,
    8,
    16,
    5,
    3,
    18,
    17,
    11,
    7,
    10,
]
KECCAK_ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]


def _rol64(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & ((1 << 64) - 1)


def _keccak_f1600(state: List[int]) -> None:
    for round_constant in KECCAK_ROUND_CONSTANTS:
        column_parity = [0] * 5
        for index in range(25):
            column_parity[index % 5] ^= state[index]

        d = [0] * 5
        for index in range(5):
            d[index] = column_parity[(index + 4) % 5] ^ _rol64(
                column_parity[(index + 1) % 5], 1
            )
        for index in range(25):
            state[index] ^= d[index % 5]

        for index, rotation in enumerate(KECCAK_ROTATIONS):
            state[index] = _rol64(state[index], rotation)

        temp = state[KECCAK_PERMUTATION[0]]
        for index in range(len(KECCAK_PERMUTATION) - 1):
            state[KECCAK_PERMUTATION[index]] = state[KECCAK_PERMUTATION[index + 1]]
        state[KECCAK_PERMUTATION[-1]] = temp

        for row in range(0, 25, 5):
            snapshot = [
                state[row],
                state[row + 1],
                state[row + 2],
                state[row + 3],
                state[row + 4],
                state[row],
                state[row + 1],
            ]
            for column in range(5):
                state[row + column] = snapshot[column] ^ (
                    (~snapshot[column + 1]) & snapshot[column + 2]
                )

        state[0] ^= round_constant


def _keccak256_pure_python(data: bytes) -> bytes:
    rate_bytes = 136
    state = [0] * 25
    offset = 0
    full_blocks = len(data) // rate_bytes

    for _ in range(full_blocks):
        block = data[offset : offset + rate_bytes]
        for lane_index in range(rate_bytes // 8):
            lane = int.from_bytes(block[lane_index * 8 : lane_index * 8 + 8], "little")
            state[lane_index] ^= lane
        offset += rate_bytes
        _keccak_f1600(state)

    final_block = bytearray(data[offset:])
    final_block.append(0x01)
    while len(final_block) < rate_bytes:
        final_block.append(0)
    final_block[-1] |= 0x80

    for lane_index in range(rate_bytes // 8):
        lane = int.from_bytes(
            final_block[lane_index * 8 : lane_index * 8 + 8], "little"
        )
        state[lane_index] ^= lane
    _keccak_f1600(state)

    output = bytearray()
    while len(output) < 32:
        for lane in state[: rate_bytes // 8]:
            output.extend(lane.to_bytes(8, "little"))
        if len(output) >= 32:
            break
        _keccak_f1600(state)
    return bytes(output[:32])


def keccak256(data: bytes) -> bytes:
    try:
        from Crypto.Hash import keccak  # type: ignore

        digest = keccak.new(digest_bits=256)
        digest.update(data)
        return digest.digest()
    except Exception:
        pass

    try:
        import sha3  # type: ignore

        return sha3.keccak_256(data).digest()
    except Exception:
        pass

    return _keccak256_pure_python(data)


# -----------------------------
# EIP-712 typed data hashing
# -----------------------------


def _is_struct_type(type_name: str, types: Dict[str, List[Dict[str, Any]]]) -> bool:
    return type_name in types and type_name != "EIP712Domain"


def _base_type(type_name: str) -> str:
    return type_name.split("[", 1)[0]


def _array_dims(type_name: str) -> List[str]:
    dims = []
    index = 0
    while True:
        start = type_name.find("[", index)
        if start < 0:
            return dims
        end = type_name.find("]", start + 1)
        if end < 0:
            return dims
        dims.append(type_name[start : end + 1])
        index = end + 1


def _field_type(field: Any) -> str:
    if isinstance(field, dict):
        value = field.get("type")
        if isinstance(value, str):
            return value
    if isinstance(field, str):
        return field
    raise Web3Error("typedData types 字段格式无效")


def _field_name(field: Any) -> str:
    if isinstance(field, dict):
        value = field.get("name")
        if isinstance(value, str):
            return value
    raise Web3Error("typedData types 字段缺少 name")


def _dependencies(primary_type: str, types: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    deps = []
    seen = set()

    def visit(type_name: str) -> None:
        for field in types.get(type_name, []):
            field_type = _base_type(_field_type(field))
            if _is_struct_type(field_type, types) and field_type not in seen:
                seen.add(field_type)
                visit(field_type)
                deps.append(field_type)

    visit(primary_type)
    deps.sort()
    return deps


def _encode_type(primary_type: str, types: Dict[str, List[Dict[str, Any]]]) -> str:
    if primary_type not in types:
        raise Web3Error("typedData 缺少类型定义: {}".format(primary_type))
    parts = [
        "{}(".format(primary_type) + ",".join(
            "{} {}".format(_field_type(field), _field_name(field)) for field in types[primary_type]
        )
        + ")"
    ]
    for dependency in _dependencies(primary_type, types):
        parts.append(
            "{}(".format(dependency)
            + ",".join(
                "{} {}".format(_field_type(field), _field_name(field)) for field in types[dependency]
            )
            + ")"
        )
    return "".join(parts)


def _infer_domain_types(domain: Dict[str, Any]) -> List[Dict[str, str]]:
    inferred = []
    canonical_order = ["name", "version", "chainId", "verifyingContract", "salt"]
    for key in canonical_order:
        if key not in domain:
            continue
        if key == "chainId":
            field_type = "uint256"
        elif key == "verifyingContract":
            field_type = "address"
        elif key == "salt":
            salt = domain[key]
            if isinstance(salt, str) and len(_clean_hex_prefix(salt)) == 64:
                field_type = "bytes32"
            elif isinstance(salt, (bytes, bytearray)) and len(salt) == 32:
                field_type = "bytes32"
            else:
                field_type = "bytes"
        else:
            field_type = "string"
        inferred.append({"name": key, "type": field_type})
    for key in domain.keys():
        if key in canonical_order:
            continue
        value = domain[key]
        if isinstance(value, bool):
            field_type = "bool"
        elif isinstance(value, int):
            field_type = "uint256"
        elif isinstance(value, (bytes, bytearray)):
            field_type = "bytes"
        else:
            field_type = "string"
        inferred.append({"name": key, "type": field_type})
    return inferred


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1"}:
            return True
        if lowered in {"false", "0"}:
            return False
    return bool(value)


def _coerce_int(value: Any, signed: bool = False) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, bytes):
        return int.from_bytes(value, "big", signed=signed)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        if _starts_with_any(text, ("0x", "0X")):
            return int(text[2:] or "0", 16)
        return int(text, 10)
    return int(value)


def _coerce_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        text = value.strip()
        if _starts_with_any(text, ("0x", "0X")):
            return _hex_to_bytes(text)
        return text.encode("utf-8")
    if isinstance(value, int):
        if value == 0:
            return b""
        width = (value.bit_length() + 7) // 8
        return value.to_bytes(width, "big")
    raise Web3Error("bytes 类型字段格式无效")


def _coerce_address(value: Any) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        if len(raw) != 20:
            raise Web3Error("地址长度不正确")
        return raw
    if isinstance(value, str):
        normalized = normalize_eth_address(value)
        if normalized is None:
            raise Web3Error("地址为空")
        return _hex_to_bytes(normalized)
    raise Web3Error("地址字段格式无效")


def _encode_primitive(field_type: str, value: Any) -> bytes:
    base_type = _base_type(field_type)
    if base_type == "address":
        return _coerce_address(value).rjust(32, b"\x00")
    if base_type == "bool":
        return (1 if _coerce_bool(value) else 0).to_bytes(32, "big")
    if base_type in {"string", "bytes"}:
        return keccak256(_coerce_bytes(value))
    if base_type.startswith("bytes") and base_type != "bytes":
        size_text = base_type[5:]
        if not size_text.isdigit():
            raise Web3Error("不支持的 typedData 字段类型: {}".format(field_type))
        size = int(size_text)
        if size < 1 or size > 32:
            raise Web3Error("不支持的 typedData 字段类型: {}".format(field_type))
        raw = _coerce_bytes(value)
        if len(raw) > size:
            raise Web3Error("typedData 字段 {} 过长".format(field_type))
        return raw.ljust(32, b"\x00")
    if base_type.startswith("uint") or base_type == "uint":
        number = _coerce_int(value)
        if number < 0:
            raise Web3Error("uint 字段不能为负数")
        return number.to_bytes(32, "big")
    if base_type.startswith("int") or base_type == "int":
        number = _coerce_int(value, signed=True)
        return number.to_bytes(32, "big", signed=True)
    if base_type == "function":
        raw = _coerce_bytes(value)
        if len(raw) != 24:
            raise Web3Error("function 字段长度不正确")
        return raw.ljust(32, b"\x00")
    raise Web3Error("不支持的 typedData 字段类型: {}".format(field_type))


def _encode_value(field_type: str, value: Any, types: Dict[str, List[Dict[str, Any]]]) -> bytes:
    dims = _array_dims(field_type)
    if dims:
        if not isinstance(value, (list, tuple)):
            raise Web3Error("typedData 数组字段格式无效: {}".format(field_type))
        base_type = _base_type(field_type)
        fixed_length = dims[0][1:-1]
        if fixed_length and int(fixed_length) != len(value):
            raise Web3Error("typedData 数组长度不正确: {}".format(field_type))
        encoded = b"".join(_encode_value(base_type + "".join(dims[1:]), item, types) for item in value)
        return keccak256(encoded)

    base_type = _base_type(field_type)
    if _is_struct_type(base_type, types):
        if not isinstance(value, dict):
            raise Web3Error("typedData 对象字段格式无效: {}".format(base_type))
        return keccak256(_encode_data(base_type, value, types))
    return _encode_primitive(field_type, value)


def _encode_data(primary_type: str, data: Dict[str, Any], types: Dict[str, List[Dict[str, Any]]]) -> bytes:
    type_hash = keccak256(_encode_type(primary_type, types).encode("utf-8"))
    encoded = bytearray(type_hash)
    for field in types[primary_type]:
        name = _field_name(field)
        field_type = _field_type(field)
        if name not in data:
            raise Web3Error("typedData 缺少字段: {}".format(name))
        encoded.extend(_encode_value(field_type, data[name], types))
    return bytes(encoded)


def _hash_struct(primary_type: str, data: Dict[str, Any], types: Dict[str, List[Dict[str, Any]]]) -> bytes:
    return keccak256(_encode_data(primary_type, data, types))


def _derive_primary_type(types: Dict[str, List[Dict[str, Any]]]) -> str:
    candidates = {name for name in types.keys() if name != "EIP712Domain"}
    for fields in types.values():
        for field in fields:
            field_type = _base_type(_field_type(field))
            if field_type in candidates:
                candidates.discard(field_type)
    if len(candidates) != 1:
        raise Web3Error("typedData 无法推导 primaryType")
    return next(iter(candidates))


def typed_data_hash(typed_data_json: str) -> bytes:
    try:
        typed_obj = json.loads(typed_data_json)
    except Exception:
        raise Web3Error("typedData 解析失败: message 不是合法 JSON")

    if not isinstance(typed_obj, dict):
        raise Web3Error("typedData 解析失败: 顶层必须是 JSON 对象")

    types_raw = typed_obj.get("types") or {}
    if not isinstance(types_raw, dict) or not types_raw:
        raise Web3Error("typedData 解析失败: 缺少 types")
    types = {
        key: list(value) if isinstance(value, list) else value for key, value in types_raw.items()
    }

    domain_data = typed_obj.get("domain") or {}
    if not isinstance(domain_data, dict):
        raise Web3Error("typedData 解析失败: domain 必须是 JSON 对象")
    message_data = typed_obj.get("message") or {}
    if not isinstance(message_data, dict):
        raise Web3Error("typedData 解析失败: message 必须是 JSON 对象")

    if "EIP712Domain" not in types:
        types["EIP712Domain"] = _infer_domain_types(domain_data)

    provided_primary_type = typed_obj.get("primaryType")
    derived_primary_type = _derive_primary_type(types)
    if provided_primary_type is not None and provided_primary_type != derived_primary_type:
        raise Web3Error("typedData 解析失败: primaryType 与推导结果不一致")

    domain_hash = _hash_struct("EIP712Domain", domain_data, types)
    message_hash = _hash_struct(derived_primary_type, message_data, types)
    return keccak256(b"\x19\x01" + domain_hash + message_hash)


# -----------------------------
# Recovery / signatures
# -----------------------------


def _recoverable_signature_parts(signature: bytes) -> Tuple[bytes, int]:
    compact, recid = secp256k1.ecdsa_recoverable_signature_serialize_compact(signature)
    return bytes(compact), int(recid)


def _normalize_recovery_id(rec_id: int) -> int:
    if 0 <= rec_id <= 1:
        return rec_id
    if 2 <= rec_id <= 3:
        return rec_id % 2
    raise Web3Error("非法 recovery id: {}".format(rec_id))


def build_eth_signature_bytes(rec_id: int, r: int, s: int) -> bytes:
    normalized = _normalize_recovery_id(rec_id)
    return _int_to_fixed_bytes(r, 32) + _int_to_fixed_bytes(s, 32) + bytes([normalized])


def build_eth_message_signature_hex(rec_id: int, r: int, s: int) -> str:
    normalized = _normalize_recovery_id(rec_id)
    v = 27 + normalized
    signature = _int_to_fixed_bytes(r, 32) + _int_to_fixed_bytes(s, 32) + bytes([v & 0xFF])
    return _ensure_hex_prefix(_bytes_hex(signature))


def _int_to_fixed_bytes(value: int, size: int) -> bytes:
    raw = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    if len(raw) > size and raw[0] == 0:
        raw = raw[1:]
    if len(raw) > size:
        raise Web3Error("Integer does not fit in {} bytes".format(size))
    return b"\x00" * (size - len(raw)) + raw


def _int_to_minimal_unsigned_bytes(value: int) -> bytes:
    if value == 0:
        return b"\x00"
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    if raw and raw[0] == 0:
        raw = raw[1:]
    return raw


def sign_digest_at_path(root_key: bip32.HDKey, derivation_path: str, digest: bytes) -> Tuple[int, int, int]:
    if len(digest) != 32:
        raise Web3Error("摘要长度必须为 32 字节")
    derived = root_key.derive(bip32.parse_path(derivation_path))
    if not derived.is_private:
        raise Web3Error("当前路径没有私钥")
    secret = derived.key.secret
    recoverable_sig = secp256k1.ecdsa_sign_recoverable(digest, secret)
    compact, recid = _recoverable_signature_parts(recoverable_sig)
    if len(compact) != 64:
        raise Web3Error("签名格式不正确")
    r = int.from_bytes(compact[:32], "big")
    s = int.from_bytes(compact[32:], "big")
    return int(recid), r, s


def personal_sign_hash(message: str | bytes) -> bytes:
    message_bytes = decode_personal_message(message)
    prefix = "\x19Ethereum Signed Message:\n{}".format(len(message_bytes)).encode("utf-8")
    return keccak256(prefix + message_bytes)


# -----------------------------
# RLP / EVM transaction helpers
# -----------------------------


def _rlp_encode_length(length: int, offset: int) -> bytes:
    if length < 56:
        return bytes([offset + length])
    len_bytes = _int_to_fixed_bytes(length, max(1, (length.bit_length() + 7) // 8)).lstrip(b"\x00")
    return bytes([offset + 55 + len(len_bytes)]) + len_bytes


def _rlp_encode_bytes(value: bytes) -> bytes:
    if len(value) == 1 and value[0] < 0x80:
        return value
    return _rlp_encode_length(len(value), 0x80) + value


def _rlp_encode_quantity(value: int) -> bytes:
    if value < 0:
        raise Web3Error("RLP 数值不能为负数")
    if value == 0:
        return _rlp_encode_bytes(b"")
    width = (value.bit_length() + 7) // 8
    return _rlp_encode_bytes(value.to_bytes(width, "big"))


def _rlp_encode_list(elements: Sequence[bytes]) -> bytes:
    payload = b"".join(elements)
    return _rlp_encode_length(len(payload), 0xC0) + payload


def _rlp_read_length(payload: bytes, offset: int, length_of_length: int) -> int:
    if length_of_length <= 0:
        raise Web3Error("RLP 长度字段不合法")
    end = offset + length_of_length
    if end > len(payload):
        raise Web3Error("RLP 长度字段越界")
    return int.from_bytes(payload[offset:end], "big")


def _rlp_decode_at(payload: bytes, offset: int) -> Tuple[Any, int]:
    if offset >= len(payload):
        raise Web3Error("RLP 数据不完整")

    prefix = payload[offset]
    if prefix <= 0x7F:
        return bytes([prefix]), offset + 1

    if prefix <= 0xB7:
        length = prefix - 0x80
        start = offset + 1
        end = start + length
        if end > len(payload):
            raise Web3Error("RLP 字节串越界")
        return payload[start:end], end

    if prefix <= 0xBF:
        length_of_length = prefix - 0xB7
        start = offset + 1
        length = _rlp_read_length(payload, start, length_of_length)
        data_start = start + length_of_length
        data_end = data_start + length
        if data_end > len(payload):
            raise Web3Error("RLP 长字节串越界")
        return payload[data_start:data_end], data_end

    if prefix <= 0xF7:
        length = prefix - 0xC0
        start = offset + 1
        end = start + length
        if end > len(payload):
            raise Web3Error("RLP 列表越界")
        return _rlp_decode_list(payload, start, end), end

    length_of_length = prefix - 0xF7
    start = offset + 1
    length = _rlp_read_length(payload, start, length_of_length)
    data_start = start + length_of_length
    data_end = data_start + length
    if data_end > len(payload):
        raise Web3Error("RLP 长列表越界")
    return _rlp_decode_list(payload, data_start, data_end), data_end


def _rlp_decode_list(payload: bytes, start: int, end: int) -> List[Any]:
    values = []
    cursor = start
    while cursor < end:
        item, cursor = _rlp_decode_at(payload, cursor)
        values.append(item)
    if cursor != end:
        raise Web3Error("RLP 列表边界不匹配")
    return values


def _rlp_decode(payload: bytes) -> Any:
    value, next_offset = _rlp_decode_at(payload, 0)
    if next_offset != len(payload):
        raise Web3Error("RLP 数据存在多余字节")
    return value


def _rlp_require_bytes(value: Any, label: str) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    raise Web3Error("{} 不是字节串".format(label))


def _rlp_require_list(value: Any, label: str) -> List[Any]:
    if isinstance(value, list):
        return value
    raise Web3Error("{} 不是列表".format(label))


def _rlp_quantity(value: Any) -> int:
    raw = _rlp_require_bytes(value, "RLP 数值")
    return int.from_bytes(raw, "big") if raw else 0


def _parse_quantity(value: Any, label: str) -> int:
    if value is None:
        return 0
    if isinstance(value, str) and not value.strip():
        return 0
    try:
        return _coerce_int(value)
    except Exception:
        raise Web3Error("{} 格式无效".format(label))


def _parse_optional_quantity(value: Any, label: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _parse_quantity(value, label)


def _parse_hex_bytes(value: Any, label: str) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return b""
        try:
            return _hex_to_bytes(text)
        except Exception:
            raise Web3Error("{} 不是合法十六进制".format(label))
    raise Web3Error("{} 格式无效".format(label))


def _parse_eth_address_bytes(value: Any, label: str) -> Optional[bytes]:
    text = _primitive_content_or_null(value)
    if text is None:
        return None
    normalized = normalize_eth_address(text)
    if normalized is None:
        return None
    try:
        raw = _hex_to_bytes(normalized)
    except Exception:
        raise Web3Error("{} 不是合法地址".format(label))
    if len(raw) != 20:
        raise Web3Error("{} 长度不正确".format(label))
    return raw


def _parse_access_list_json(value: Any) -> List[EvmAccessListEntry]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise Web3Error("accessList 格式无效")

    entries = []
    for item in value:
        if not isinstance(item, dict):
            raise Web3Error("accessList 条目格式无效")
        address = _parse_eth_address_bytes(item.get("address"), "accessList.address")
        if address is None:
            raise Web3Error("accessList.address 缺失")
        storage_keys_raw = item.get("storageKeys") or []
        if not isinstance(storage_keys_raw, (list, tuple)):
            raise Web3Error("accessList.storageKeys 格式无效")
        storage_keys = [_parse_hex_bytes(storage_key, "storageKey") for storage_key in storage_keys_raw if storage_key is not None]
        entries.append(EvmAccessListEntry(address=address, storage_keys=storage_keys))
    return entries


def _parse_access_list_rlp(value: Any) -> List[EvmAccessListEntry]:
    entries = []
    for item in _rlp_require_list(value, "accessList"):
        entry = _rlp_require_list(item, "accessList entry")
        if len(entry) != 2:
            raise Web3Error("accessList entry 格式错误")
        address = _rlp_require_bytes(entry[0], "accessList.address")
        if len(address) != 20:
            raise Web3Error("accessList.address 长度不正确")
        storage_keys = [_rlp_require_bytes(storage_key, "storageKey") for storage_key in _rlp_require_list(entry[1], "accessList.storageKeys")]
        entries.append(EvmAccessListEntry(address=address, storage_keys=storage_keys))
    return entries


def _parse_tx_type(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (bytes, bytearray)):
        text = _maybe_text(bytes(value))
        if text is None:
            raise Web3Error("交易 type 格式无效")
        value = text
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        if _starts_with_any(text, ("0x", "0X")):
            return int(text[2:] or "0", 16)
        return int(text, 10)
    raise Web3Error("交易 type 格式无效")


def _parse_tp_transaction_request(tx_data: Dict[str, Any], chain_id: int) -> EvmUnsignedTransaction:
    tx_type = _parse_tx_type(tx_data.get("type"))
    if tx_type not in (0, 1, 2):
        raise Web3Error("暂不支持的交易类型: {}".format(tx_type))

    nonce = _parse_quantity(tx_data.get("nonce"), "nonce")
    gas_limit = _parse_quantity(
        _first_non_blank(
            _primitive_content_or_null(tx_data.get("gas")),
            _primitive_content_or_null(tx_data.get("gasLimit")),
        ),
        "gasLimit",
    )
    to = _parse_eth_address_bytes(tx_data.get("to"), "to")
    value = _parse_quantity(tx_data.get("value"), "value")
    data_hex = _first_non_blank(
        _primitive_content_or_null(tx_data.get("data")),
        _primitive_content_or_null(tx_data.get("input")),
        "0x",
    )
    data = _parse_hex_bytes(data_hex, "data")
    gas_price = _parse_optional_quantity(tx_data.get("gasPrice"), "gasPrice")
    max_priority_fee_per_gas = _parse_optional_quantity(tx_data.get("maxPriorityFeePerGas"), "maxPriorityFeePerGas")
    max_fee_per_gas = _parse_optional_quantity(tx_data.get("maxFeePerGas"), "maxFeePerGas")
    access_list = _parse_access_list_json(tx_data.get("accessList"))

    if tx_type in (0, 1) and gas_price is None:
        raise Web3Error("Legacy / EIP-2930 交易缺少 gasPrice")
    if tx_type == 2 and (max_priority_fee_per_gas is None or max_fee_per_gas is None):
        raise Web3Error("EIP-1559 交易缺少 maxPriorityFeePerGas / maxFeePerGas")

    return EvmUnsignedTransaction(
        tx_type=tx_type,
        chain_id=int(chain_id or 0),
        nonce=nonce,
        gas_limit=gas_limit,
        to=to,
        value=value,
        data=data,
        gas_price=gas_price,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        max_fee_per_gas=max_fee_per_gas,
        access_list=access_list if tx_type in (1, 2) else [],
    )


def _parse_unsigned_transaction_bytes(
    sign_data: bytes,
    data_type: Web3RequestDataType,
    chain_id: int,
) -> EvmUnsignedTransaction:
    if not sign_data:
        raise Web3Error("交易签名数据为空")

    if data_type == Web3RequestDataType.TRANSACTION:
        values = _rlp_require_list(_rlp_decode(sign_data), "Legacy unsigned tx")
        if len(values) < 6:
            raise Web3Error("Legacy unsigned tx 字段不足")
        tx_chain_id = _rlp_quantity(values[6]) if len(values) > 6 else int(chain_id or 0)
        return EvmUnsignedTransaction(
            tx_type=0,
            chain_id=tx_chain_id or int(chain_id or 0),
            nonce=_rlp_quantity(values[0]),
            gas_limit=_rlp_quantity(values[2]),
            to=_rlp_require_bytes(values[3], "to") or None,
            value=_rlp_quantity(values[4]),
            data=_rlp_require_bytes(values[5], "data"),
            gas_price=_rlp_quantity(values[1]),
            access_list=[],
        )

    if data_type == Web3RequestDataType.TYPED_TRANSACTION:
        tx_type = sign_data[0]
        body = sign_data[1:]
        values = _rlp_require_list(_rlp_decode(body), "Typed unsigned tx")
        if tx_type == 0x01:
            if len(values) < 8:
                raise Web3Error("EIP-2930 unsigned tx 字段不足")
            return EvmUnsignedTransaction(
                tx_type=1,
                chain_id=_rlp_quantity(values[0]) or int(chain_id or 0),
                nonce=_rlp_quantity(values[1]),
                gas_limit=_rlp_quantity(values[3]),
                to=_rlp_require_bytes(values[4], "to") or None,
                value=_rlp_quantity(values[5]),
                data=_rlp_require_bytes(values[6], "data"),
                gas_price=_rlp_quantity(values[2]),
                access_list=_parse_access_list_rlp(values[7]),
            )
        if tx_type == 0x02:
            if len(values) < 9:
                raise Web3Error("EIP-1559 unsigned tx 字段不足")
            return EvmUnsignedTransaction(
                tx_type=2,
                chain_id=_rlp_quantity(values[0]) or int(chain_id or 0),
                nonce=_rlp_quantity(values[1]),
                gas_limit=_rlp_quantity(values[4]),
                to=_rlp_require_bytes(values[5], "to") or None,
                value=_rlp_quantity(values[6]),
                data=_rlp_require_bytes(values[7], "data"),
                max_priority_fee_per_gas=_rlp_quantity(values[2]),
                max_fee_per_gas=_rlp_quantity(values[3]),
                access_list=_parse_access_list_rlp(values[8]),
            )
        raise Web3Error("当前暂不支持的 typed transaction 类型: 0x{:02x}".format(tx_type))

    raise Web3Error("当前请求不是交易类型")


def _encode_access_list(access_list: Sequence[EvmAccessListEntry]) -> bytes:
    entries = []
    for entry in access_list:
        storage_keys = [_rlp_encode_bytes(storage_key) for storage_key in entry.storage_keys]
        entries.append(_rlp_encode_list([_rlp_encode_bytes(entry.address), _rlp_encode_list(storage_keys)]))
    return _rlp_encode_list(entries)


def _encode_unsigned_transaction(tx: EvmUnsignedTransaction) -> bytes:
    if tx.tx_type == 0:
        fields = [
            _rlp_encode_quantity(tx.nonce),
            _rlp_encode_quantity(tx.gas_price or 0),
            _rlp_encode_quantity(tx.gas_limit),
            _rlp_encode_bytes(tx.to or b""),
            _rlp_encode_quantity(tx.value),
            _rlp_encode_bytes(tx.data),
            _rlp_encode_quantity(tx.chain_id),
            _rlp_encode_quantity(0),
            _rlp_encode_quantity(0),
        ]
        return _rlp_encode_list(fields)

    if tx.tx_type == 1:
        fields = [
            _rlp_encode_quantity(tx.chain_id),
            _rlp_encode_quantity(tx.nonce),
            _rlp_encode_quantity(tx.gas_price or 0),
            _rlp_encode_quantity(tx.gas_limit),
            _rlp_encode_bytes(tx.to or b""),
            _rlp_encode_quantity(tx.value),
            _rlp_encode_bytes(tx.data),
            _encode_access_list(tx.access_list),
        ]
        return b"\x01" + _rlp_encode_list(fields)

    if tx.tx_type == 2:
        fields = [
            _rlp_encode_quantity(tx.chain_id),
            _rlp_encode_quantity(tx.nonce),
            _rlp_encode_quantity(tx.max_priority_fee_per_gas or 0),
            _rlp_encode_quantity(tx.max_fee_per_gas or 0),
            _rlp_encode_quantity(tx.gas_limit),
            _rlp_encode_bytes(tx.to or b""),
            _rlp_encode_quantity(tx.value),
            _rlp_encode_bytes(tx.data),
            _encode_access_list(tx.access_list),
        ]
        return b"\x02" + _rlp_encode_list(fields)

    raise Web3Error("暂不支持的交易类型: {}".format(tx.tx_type))


def _encode_signed_transaction(tx: EvmUnsignedTransaction, rec_id: int, r: int, s: int) -> bytes:
    normalized_rec_id = _normalize_recovery_id(rec_id)
    if tx.tx_type == 0:
        v = tx.chain_id * 2 + 35 + normalized_rec_id
        fields = [
            _rlp_encode_quantity(tx.nonce),
            _rlp_encode_quantity(tx.gas_price or 0),
            _rlp_encode_quantity(tx.gas_limit),
            _rlp_encode_bytes(tx.to or b""),
            _rlp_encode_quantity(tx.value),
            _rlp_encode_bytes(tx.data),
            _rlp_encode_quantity(v),
            _rlp_encode_quantity(r),
            _rlp_encode_quantity(s),
        ]
        return _rlp_encode_list(fields)

    if tx.tx_type == 1:
        fields = [
            _rlp_encode_quantity(tx.chain_id),
            _rlp_encode_quantity(tx.nonce),
            _rlp_encode_quantity(tx.gas_price or 0),
            _rlp_encode_quantity(tx.gas_limit),
            _rlp_encode_bytes(tx.to or b""),
            _rlp_encode_quantity(tx.value),
            _rlp_encode_bytes(tx.data),
            _encode_access_list(tx.access_list),
            _rlp_encode_quantity(normalized_rec_id),
            _rlp_encode_quantity(r),
            _rlp_encode_quantity(s),
        ]
        return b"\x01" + _rlp_encode_list(fields)

    if tx.tx_type == 2:
        fields = [
            _rlp_encode_quantity(tx.chain_id),
            _rlp_encode_quantity(tx.nonce),
            _rlp_encode_quantity(tx.max_priority_fee_per_gas or 0),
            _rlp_encode_quantity(tx.max_fee_per_gas or 0),
            _rlp_encode_quantity(tx.gas_limit),
            _rlp_encode_bytes(tx.to or b""),
            _rlp_encode_quantity(tx.value),
            _rlp_encode_bytes(tx.data),
            _encode_access_list(tx.access_list),
            _rlp_encode_quantity(normalized_rec_id),
            _rlp_encode_quantity(r),
            _rlp_encode_quantity(s),
        ]
        return b"\x02" + _rlp_encode_list(fields)

    raise Web3Error("暂不支持的交易类型: {}".format(tx.tx_type))


def _transaction_type_label(tx_type: int) -> str:
    if tx_type == 0:
        return "传统"
    if tx_type == 1:
        return "EIP-2930"
    if tx_type == 2:
        return "EIP-1559"
    return "0x{:02x}".format(tx_type)


# -----------------------------
# TP request parsing and responses
# -----------------------------


def normalize_action(action: str) -> str:
    return "".join(char for char in action.lower() if char not in "-_ ")


def _parse_optional_chain_id(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        value = text.split(":")[-1]
        if _starts_with_any(value, ("0x", "0X")):
            return int(value[2:] or "0", 16)
        return int(value, 10)
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    try:
        text = str(raw).strip()
        if not text:
            return None
        if _starts_with_any(text, ("0x", "0X")):
            return int(text[2:] or "0", 16)
        return int(text, 10)
    except Exception:
        return None


def _parse_query(query_raw: str) -> Dict[str, str]:
    out = {}
    marker = query_raw.find("data=")
    if marker >= 0:
        before = query_raw[:marker]
        if before:
            for piece in before.split("&"):
                if not piece or "=" not in piece:
                    continue
                key, value = piece.split("=", 1)
                out[key] = _smart_decode(value)
        out["data"] = _smart_decode(query_raw[marker + 5 :])
        return out

    for piece in query_raw.split("&"):
        if not piece or "=" not in piece:
            continue
        key, value = piece.split("=", 1)
        out[key] = _smart_decode(value)
    return out


def _smart_decode(value: str) -> str:
    try:
        return _url_unquote(value)
    except Exception:
        return value


def _url_unquote(value: str) -> str:
    data = bytearray()
    index = 0
    while index < len(value):
        char = value[index]
        if char == "%" and index + 2 < len(value):
            try:
                data.append(int(value[index + 1 : index + 3], 16))
                index += 3
                continue
            except Exception:
                pass
        if char == "+":
            data.append(32)
        else:
            data.extend(char.encode("utf-8"))
        index += 1
    return bytes(data).decode("utf-8")


def _extract_typed_data_json(message_element: Any) -> str:
    if isinstance(message_element, (dict, list)):
        text = _json_dumps_compact(message_element)
    elif isinstance(message_element, str):
        text = message_element.strip()
    else:
        raise Web3Error("typedData message 格式无效")

    if not (text.startswith("{") or text.startswith("[")):
        raise Web3Error("typedData message 必须是 JSON 字符串")

    try:
        json.loads(text)
    except Exception:
        raise Web3Error("typedData message 不是合法 JSON")
    return text


def _parse_request_context(raw: str) -> Tuple[str, str, str, Dict[str, str], Dict[str, Any]]:
    dash = raw.find("-")
    if dash <= 0:
        raise Web3Error("不是受支持的请求字符串")

    left = raw[:dash]
    namespace = left.split(":", 1)[0]
    action = left.split(":", 1)[1] if ":" in left else ""
    if not namespace or not action:
        raise Web3Error("协议前缀不合法")

    query_raw = raw[dash + 1 :]
    if query_raw.startswith("?"):
        query_raw = query_raw[1:]
    params = _parse_query(query_raw)
    data_raw = params.get("data")
    if data_raw is None:
        raise Web3Error("缺少 data 字段")
    try:
        data_json = json.loads(data_raw)
    except Exception:
        raise Web3Error("data JSON 无效")
    if not isinstance(data_json, dict):
        raise Web3Error("data JSON 必须是对象")
    return namespace, action, data_raw, params, data_json


def parse_tp_multi_fragment(raw: str) -> TpMultiFragment:
    normalized = raw.strip()
    if not normalized.lower().startswith("tp:multifragment-"):
        raise Web3Error("不是 tp:multiFragment 分片")

    dash = normalized.find("-")
    if dash <= 0:
        raise Web3Error("无效分片格式")

    query_raw = normalized[dash + 1 :]
    if query_raw.startswith("?"):
        query_raw = query_raw[1:]
    params = _parse_query(query_raw)
    data_raw = params.get("data")
    if not data_raw:
        raise Web3Error("分片缺少 data")
    try:
        data = json.loads(data_raw)
    except Exception as exc:
        raise Web3Error("分片 data JSON 无效: {}".format(exc))
    if not isinstance(data, dict):
        raise Web3Error("分片 data JSON 必须是对象")

    content = str(data.get("content") or "")
    if not content:
        raise Web3Error("分片缺少 content")
    index, total = _parse_fragment_position(data)
    split = content.rfind("_")
    if split <= 0 or split >= len(content) - 1:
        raise Web3Error("分片 content 格式无效")
    return TpMultiFragment(
        index=index,
        total=total,
        chunk=content[:split],
        crc32=content[split + 1 :],
    )


def _decode_relay_base64(encoded: str) -> bytes:
    normalized = "".join(str(encoded or "").split())
    lowered = normalized.lower()
    if lowered.startswith("data:"):
        comma = normalized.rfind(",")
        if comma >= 0:
            normalized = normalized[comma + 1 :]
    normalized = normalized.replace("-", "+").replace("_", "/")
    padding = len(normalized) % 4
    if padding:
        normalized += "=" * (4 - padding)
    try:
        return a2b_base64(normalized)
    except Exception:
        raise Web3Error("中转二维码 Base64 解码失败")


def _looks_like_relay_text(text: str) -> bool:
    lowered = text.strip().lower()
    return _starts_with_any(
        lowered,
        (
            "tp:",
            "ur:",
            "{",
            "[",
            "ethereum:",
            "wc:",
        ),
    )


def _relay_text_candidates(text: str) -> List[str]:
    candidates = []
    current = str(text or "").strip()
    for _ in range(3):
        if current and current not in candidates:
            candidates.append(current)
            if (
                len(current) >= 2
                and (
                    (current[0] == '"' and current[-1] == '"')
                    or (current[0] == "'" and current[-1] == "'")
                )
            ):
                unquoted = current[1:-1].strip()
                if unquoted and unquoted not in candidates:
                    candidates.append(unquoted)
        decoded = _smart_decode(current).strip()
        if decoded == current:
            break
        current = decoded
    return candidates


def _relay_base64_candidates(encoded: str) -> List[str]:
    candidates = []
    for text in _relay_text_candidates(str(encoded or "")):
        cleaned = "".join(text.split())
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)
        lowered = cleaned.lower()
        if lowered.startswith("base64,"):
            payload = cleaned[7:]
            if payload and payload not in candidates:
                candidates.append(payload)
        comma = cleaned.rfind(",")
        if lowered.startswith("data:") and comma >= 0:
            payload = cleaned[comma + 1 :]
            if payload and payload not in candidates:
                candidates.append(payload)
        for marker in ("data=", "payload=", "content="):
            pos = lowered.find(marker)
            if pos >= 0:
                payload = cleaned[pos + len(marker) :]
                separator = payload.find("&")
                if separator >= 0:
                    payload = payload[:separator]
                if payload and payload not in candidates:
                    candidates.append(payload)
    return candidates


def _decode_relay_text_bytes(raw: bytes) -> Optional[str]:
    for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = raw.decode(encoding).strip()
            for candidate in _relay_text_candidates(text):
                if _looks_like_relay_text(candidate):
                    return candidate
        except Exception:
            pass
    return None


def _gzip_decompress(compressed: bytes) -> bytes:
    if len(compressed) < 18 or compressed[0] != 0x1F or compressed[1] != 0x8B:
        raise Web3Error("不是 gzip 数据")
    if compressed[2] != 8:
        raise Web3Error("gzip 压缩方式不支持")

    flags = compressed[3]
    index = 10
    if flags & 4:
        if index + 2 > len(compressed):
            raise Web3Error("gzip 扩展头无效")
        extra_len = compressed[index] | (compressed[index + 1] << 8)
        index += 2 + extra_len
    if flags & 8:
        while index < len(compressed) and compressed[index] != 0:
            index += 1
        index += 1
    if flags & 16:
        while index < len(compressed) and compressed[index] != 0:
            index += 1
        index += 1
    if flags & 2:
        index += 2
    if index >= len(compressed) - 8:
        raise Web3Error("gzip 内容为空")

    return _raw_deflate_decompress(compressed[index:-8])


def _inflate_relay_text(encoded: str) -> str:
    for plain_text in _relay_text_candidates(str(encoded or "")):
        if _looks_like_relay_text(plain_text):
            return plain_text

    for candidate in _relay_base64_candidates(encoded):
        try:
            compressed = _decode_relay_base64(candidate)
        except Web3Error:
            continue

        decoded_text = _decode_relay_text_bytes(compressed)
        if decoded_text is not None:
            return decoded_text

        for decompressor in (
            _deflateio_decompress_auto,
            _gzip_decompress_with_zlib,
            _zlib_decompress,
            _deflateio_decompress_zlib,
            lambda data: _zlib_decompress(data, raw=True),
            _deflateio_decompress_raw,
            _gzip_decompress,
            _deflateio_decompress_gzip,
        ):
            try:
                raw = decompressor(compressed)
            except Exception:
                continue
            decoded_text = _decode_relay_text_bytes(raw)
            if decoded_text is not None:
                return decoded_text
    raise Web3Error("中转二维码解压失败")


def inflate_relay_text(encoded: str) -> str:
    return _inflate_relay_text(encoded)


def parse_relay_fragment(raw: str) -> RelayFragment:
    normalized = raw.strip()
    lowered = normalized.lower()
    if lowered.startswith(RELAY_TP_PREFIX):
        prefix = RELAY_TP_PREFIX
    elif lowered.startswith(RELAY_WEB3_PREFIX):
        prefix = RELAY_WEB3_PREFIX
    else:
        raise Web3Error("不是受支持的中转二维码分片")

    body = normalized[len(prefix) :]
    first_dot = body.find(".")
    second_dot = body.find(".", first_dot + 1)
    slash = body.find("/")
    if slash <= 0 or first_dot <= slash or second_dot <= first_dot:
        raise Web3Error("中转分片格式无效")

    try:
        index = int(body[:slash])
        total = int(body[slash + 1 : first_dot])
    except Exception:
        raise Web3Error("中转分片序号无效")

    crc32 = body[first_dot + 1 : second_dot].strip()
    chunk = body[second_dot + 1 :].strip()
    if not crc32 or not chunk:
        raise Web3Error("中转分片缺少 CRC 或内容")
    return RelayFragment(
        prefix=prefix,
        index=index,
        total=total,
        chunk=chunk,
        crc32=crc32,
    )


def decode_relay_payload(raw: str) -> Tuple[str, str]:
    fragment = parse_relay_fragment(raw)
    assembler = RelayFragmentAssembler(fragment.prefix)
    state, detail = assembler.accept(fragment)
    if state != "complete" or detail is None:
        raise Web3Error("中转二维码需要完整分片后才能解析")
    return fragment.prefix, _inflate_relay_text(detail)


def parse_web3_relay_envelope(payload: str) -> Web3RelayEnvelope:
    try:
        data = json.loads(payload)
    except Exception:
        raise Web3Error("链上中转包 JSON 无效")
    if not isinstance(data, dict):
        raise Web3Error("链上中转包必须是对象")

    raw_payload = str(data.get("payload") or "").strip()
    if not raw_payload:
        raise Web3Error("链上中转包缺少载荷")

    chain_id_value = data.get("chain_id")
    parsed_chain_id = None
    if chain_id_value not in (None, ""):
        try:
            parsed_chain_id = int(chain_id_value)
        except Exception:
            parsed_chain_id = None

    request_type_value = data.get("request_data_type_id")
    parsed_request_type = None
    if request_type_value not in (None, ""):
        try:
            parsed_request_type = int(request_type_value)
        except Exception:
            parsed_request_type = None

    return Web3RelayEnvelope(
        wallet=str(data.get("wallet") or "").strip() or "W3R",
        wallet_name=str(
            data.get("wallet_name") or data.get("wallet") or "链上桥接"
        ).strip(),
        detected_format=_primitive_content_or_null(data.get("format")),
        qr_type=_primitive_content_or_null(data.get("qr_type")),
        action=_primitive_content_or_null(data.get("action")),
        chain=_primitive_content_or_null(data.get("chain")),
        payload=raw_payload,
        response_protocol=_primitive_content_or_null(data.get("response_protocol")),
        request_id=_primitive_content_or_null(data.get("request_id")),
        origin=_primitive_content_or_null(data.get("origin")),
        data_type_name=_primitive_content_or_null(data.get("data_type")),
        request_data_type_id=parsed_request_type,
        request_sign_data_hex=_primitive_content_or_null(data.get("request_sign_data_hex")),
        chain_id=parsed_chain_id,
        address=_primitive_content_or_null(data.get("address")),
        address_path=_primitive_content_or_null(data.get("address_path")),
        expected_address=_primitive_content_or_null(data.get("expected_address")),
    )


def _parse_fragment_position(data: Dict[str, Any]) -> Tuple[int, int]:
    index_raw = str(data.get("index") or "").strip()
    total_raw = (
        str(data.get("total") or "").strip()
        or str(data.get("count") or "").strip()
        or str(data.get("size") or "").strip()
    )

    if index_raw:
        pair = _parse_index_total(index_raw)
        if pair is not None:
            return pair
        if total_raw:
            return int(index_raw), int(total_raw)

    raise Web3Error("分片缺少 index/total 信息")


def _parse_index_total(value: str) -> Optional[Tuple[int, int]]:
    if "/" in value:
        left, right = value.split("/", 1)
        return int(left.strip()), int(right.strip())
    if "-" in value:
        left, right = value.split("-", 1)
        return int(left.strip()), int(right.strip())
    return None


def parse_tp_request(raw: str) -> TpParsedRequest:
    namespace, action, raw_data, params, data_json = _parse_request_context(raw)
    normalized_action = normalize_action(action)
    request_format = "legacy" if ("v" in params or "action" in params) else "modern"
    version = params.get("version") or params.get("v") or "1.0"
    protocol = params.get("protocol") or "ArbitrumWallet"
    network = params.get("network") or "ethereum"
    chain_id_raw = params.get("chain_id") or params.get("blockchainId")

    dapp = data_json.get("dapp")
    dapp_name = _first_non_blank(
        _primitive_content_or_null(data_json.get("dappName")),
        _primitive_content_or_null(dapp.get("name")) if isinstance(dapp, dict) else None,
        _primitive_content_or_null(data_json.get("name")),
    )
    dapp_url = _first_non_blank(
        _primitive_content_or_null(data_json.get("dappUrl")),
        _primitive_content_or_null(data_json.get("url")),
        _primitive_content_or_null(data_json.get("website")),
        _primitive_content_or_null(dapp.get("url")) if isinstance(dapp, dict) else None,
    )
    dapp_source = _first_non_blank(
        _primitive_content_or_null(data_json.get("origin")),
        _primitive_content_or_null(data_json.get("source")),
        _primitive_content_or_null(data_json.get("host")),
        params.get("source"),
    )

    if normalized_action in TRANSACTION_ACTIONS:
        tx_data = data_json.get("txData")
        if not isinstance(tx_data, dict):
            tx_data = data_json
        tx_type = _parse_tx_type(_primitive_content_or_null(tx_data.get("type")))
        if tx_type not in (0, 1, 2):
            raise Web3Error("暂不支持的交易类型: {}".format(tx_type))
        address = _first_non_blank(
            _primitive_content_or_null(data_json.get("address")),
            _primitive_content_or_null(tx_data.get("from")) if isinstance(tx_data, dict) else None,
            _primitive_content_or_null(tx_data.get("fromAddress")) if isinstance(tx_data, dict) else None,
        )
        chain_id = (
            _parse_optional_chain_id(_primitive_content_or_null(tx_data.get("chainId")))
            if isinstance(tx_data, dict)
            else None
        ) or _parse_optional_chain_id(chain_id_raw) or 1
        return TpParsedRequest(
            raw_payload=raw,
            namespace=namespace,
            action=action,
            request_format=request_format,
            version=version,
            protocol=protocol,
            network=network,
            chain_id=chain_id,
            request_id=params.get("requestId"),
            action_id=params.get("actionId"),
            data_id=_primitive_content_or_null(data_json.get("id")),
            dapp_name=dapp_name,
            dapp_url=dapp_url,
            dapp_source=dapp_source,
            address=normalize_eth_address(address) if address else None,
            kind="typed_transaction" if tx_type in (1, 2) else "transaction",
            message=None,
            typed_data_json=None,
            tx_data=tx_data,
        )

    if normalized_action in PERSONAL_ACTIONS:
        message = data_json.get("message")
        if message is None:
            raise Web3Error("personalSign 缺少 message 字段")
        message_text = _primitive_content_or_null(message)
        if message_text is None:
            message_text = str(message)
        address = _primitive_content_or_null(data_json.get("address"))
        chain_id = _parse_optional_chain_id(chain_id_raw) or 1
        return TpParsedRequest(
            raw_payload=raw,
            namespace=namespace,
            action=action,
            request_format=request_format,
            version=version,
            protocol=protocol,
            network=network,
            chain_id=chain_id,
            request_id=params.get("requestId"),
            action_id=params.get("actionId"),
            data_id=_primitive_content_or_null(data_json.get("id")),
            dapp_name=dapp_name,
            dapp_url=dapp_url,
            dapp_source=dapp_source,
            address=normalize_eth_address(address) if address else None,
            kind="personal_message",
            message=message_text,
            typed_data_json=None,
            tx_data=None,
        )

    if normalized_action in TYPED_DATA_ACTIONS:
        message_element = data_json.get("message")
        if message_element is None:
            raise Web3Error("signTypedData 缺少 message 字段")
        typed_data_json = _extract_typed_data_json(message_element)
        chain_from_domain = _typed_data_domain_chain_id(typed_data_json)
        chain_id = _parse_optional_chain_id(chain_id_raw) or chain_from_domain or 1
        address = _primitive_content_or_null(data_json.get("address"))
        return TpParsedRequest(
            raw_payload=raw,
            namespace=namespace,
            action=action,
            request_format=request_format,
            version=version,
            protocol=protocol,
            network=network,
            chain_id=chain_id,
            request_id=params.get("requestId"),
            action_id=params.get("actionId"),
            data_id=_primitive_content_or_null(data_json.get("id")),
            dapp_name=dapp_name,
            dapp_url=dapp_url,
            dapp_source=dapp_source,
            address=normalize_eth_address(address) if address else None,
            kind="typed_data",
            message=None,
            typed_data_json=typed_data_json,
            tx_data=None,
        )

    raise Web3Error("当前仅支持 signTransaction / personalSign / signTypedData")


def _typed_data_domain_chain_id(typed_data_json: str) -> Optional[int]:
    try:
        parsed = json.loads(typed_data_json)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    domain = parsed.get("domain")
    if not isinstance(domain, dict):
        return None
    return _parse_optional_chain_id(domain.get("chainId"))


def _primitive_content_or_null(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (bytes, bytearray)):
        text = _maybe_text(bytes(value))
        if text is not None:
            return text
        return _bytes_hex(value)
    return str(value)


def _first_non_blank(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value is not None and value.strip():
            return value.strip()
    return None


def _looks_like_eth_address(value: Any) -> bool:
    text = _primitive_content_or_null(value)
    if text is None:
        return False
    clean = _clean_hex_prefix(text.strip())
    if len(clean) != 40:
        return False
    for char in clean:
        if char not in "0123456789abcdefABCDEF":
            return False
    return True


def _json_rpc_params(params: Any) -> Any:
    if isinstance(params, dict):
        return params
    if isinstance(params, (list, tuple)):
        return list(params)
    if params is None:
        return []
    return [params]


def _json_rpc_param(params: Any, key: str, index: int = 0) -> Any:
    if isinstance(params, dict):
        return params.get(key)
    return None


def _json_rpc_chain_id(
    data: Dict[str, Any],
    params: Any,
    tx_data: Optional[Dict[str, Any]] = None,
) -> int:
    candidates = [
        data.get("chainId"),
        data.get("chain_id"),
        data.get("chain"),
        _json_rpc_param(params, "chainId"),
        _json_rpc_param(params, "chain_id"),
    ]
    if isinstance(tx_data, dict):
        candidates.extend([tx_data.get("chainId"), tx_data.get("chain_id")])
    for candidate in candidates:
        parsed = _parse_optional_chain_id(candidate)
        if parsed is not None:
            return parsed
    return 1


def _json_rpc_origin(data: Dict[str, Any], params: Any) -> Optional[str]:
    return _first_non_blank(
        _primitive_content_or_null(data.get("origin")),
        _primitive_content_or_null(data.get("source")),
        _primitive_content_or_null(data.get("dappName")),
        _primitive_content_or_null(data.get("name")),
        _primitive_content_or_null(data.get("url")),
        _primitive_content_or_null(_json_rpc_param(params, "origin")),
        _primitive_content_or_null(_json_rpc_param(params, "source")),
        _primitive_content_or_null(_json_rpc_param(params, "dappName")),
    )


def _json_rpc_request_id(data: Dict[str, Any]) -> Optional[str]:
    return _parse_request_id_text(
        data.get("requestId")
        if data.get("requestId") is not None
        else data.get("id")
    )


def _json_rpc_tp_request(
    raw: str,
    action: str,
    kind: str,
    chain_id: int,
    request_id: Optional[str],
    origin: Optional[str],
    address: Optional[str],
    message: Optional[str] = None,
    typed_data_json: Optional[str] = None,
    tx_data: Optional[Dict[str, Any]] = None,
) -> TpParsedRequest:
    return TpParsedRequest(
        raw_payload=raw,
        namespace="tp",
        action=action,
        request_format="modern",
        version="1.0",
        protocol="ArbitrumWallet",
        network="ethereum",
        chain_id=chain_id,
        request_id=request_id,
        action_id=request_id,
        data_id=request_id,
        dapp_name=origin,
        dapp_url=None,
        dapp_source=origin,
        address=address,
        kind=kind,
        message=message,
        typed_data_json=typed_data_json,
        tx_data=tx_data,
    )


def parse_json_rpc_web3_request(payload: str) -> Web3Request:
    """Parse common Ethereum JSON-RPC signing requests scanned from wallets."""
    try:
        data = json.loads(payload)
    except Exception:
        raise Web3Error("JSON-RPC 请求不是合法 JSON")
    if not isinstance(data, dict):
        raise Web3Error("JSON-RPC 请求必须是对象")

    method = _primitive_content_or_null(data.get("method") or data.get("action"))
    if method is None:
        raise Web3Error("JSON-RPC 请求缺少 method")
    normalized_method = normalize_action(method)
    params = _json_rpc_params(data.get("params", data.get("parameters")))
    origin = _json_rpc_origin(data, params)
    request_id = _json_rpc_request_id(data)
    derivation_path = _normalize_path(
        _first_non_blank(
            _primitive_content_or_null(data.get("address_path")),
            _primitive_content_or_null(data.get("addressPath")),
            _primitive_content_or_null(data.get("derivation_path")),
            _primitive_content_or_null(_json_rpc_param(params, "path")),
            _primitive_content_or_null(_json_rpc_param(params, "addressPath")),
        )
    )

    if normalized_method in TRANSACTION_ACTIONS:
        tx_data = _json_rpc_param(params, "txData")
        if not isinstance(tx_data, dict):
            tx_data = _json_rpc_param(params, "transaction")
        if not isinstance(tx_data, dict) and isinstance(params, list) and params:
            tx_data = params[0]
        if not isinstance(tx_data, dict):
            raise Web3Error("JSON-RPC 交易请求缺少交易对象")
        tx_type = _parse_tx_type(tx_data.get("type"))
        chain_id = _json_rpc_chain_id(data, params, tx_data)
        address = _first_non_blank(
            _primitive_content_or_null(tx_data.get("from")),
            _primitive_content_or_null(tx_data.get("fromAddress")),
            _primitive_content_or_null(data.get("address")),
        )
        normalized_address = normalize_eth_address(address) if address else None
        kind = "typed_transaction" if tx_type in (1, 2) else "transaction"
        data_type = (
            Web3RequestDataType.TYPED_TRANSACTION
            if kind == "typed_transaction"
            else Web3RequestDataType.TRANSACTION
        )
        tp_request = _json_rpc_tp_request(
            payload,
            "signTransaction",
            kind,
            chain_id,
            request_id,
            origin,
            normalized_address,
            tx_data=tx_data,
        )
        return Web3Request(
            source_format="json-rpc",
            data_type=data_type,
            chain_id=chain_id,
            derivation_path=derivation_path,
            address=normalized_address,
            origin=origin,
            request_id_value=request_id,
            request_id_text=request_id,
            sign_data=_json_dumps_compact(tx_data).encode("utf-8"),
            raw_payload=payload,
            tp_request=tp_request,
        )

    if normalized_method in PERSONAL_ACTIONS:
        if isinstance(params, dict):
            address = _first_non_blank(
                _primitive_content_or_null(params.get("address")),
                _primitive_content_or_null(params.get("account")),
            )
            message_value = params.get("message", params.get("data"))
        else:
            first = params[0] if len(params) > 0 else None
            second = params[1] if len(params) > 1 else None
            if normalized_method == "ethsign" or _looks_like_eth_address(first):
                address = _primitive_content_or_null(first)
                message_value = second
            else:
                message_value = first
                address = _primitive_content_or_null(second)
        message_text = _primitive_content_or_null(message_value)
        if message_text is None:
            raise Web3Error("JSON-RPC personal_sign 缺少消息")
        normalized_address = normalize_eth_address(address) if address else None
        chain_id = _json_rpc_chain_id(data, params)
        tp_request = _json_rpc_tp_request(
            payload,
            "personalSign",
            "personal_message",
            chain_id,
            request_id,
            origin,
            normalized_address,
            message=message_text,
        )
        return Web3Request(
            source_format="json-rpc",
            data_type=Web3RequestDataType.PERSONAL_MESSAGE,
            chain_id=chain_id,
            derivation_path=derivation_path,
            address=normalized_address,
            origin=origin,
            request_id_value=request_id,
            request_id_text=request_id,
            sign_data=decode_personal_message(message_text),
            raw_payload=payload,
            message_text=message_text,
            tp_request=tp_request,
        )

    if normalized_method in TYPED_DATA_ACTIONS:
        if isinstance(params, dict):
            address = _first_non_blank(
                _primitive_content_or_null(params.get("address")),
                _primitive_content_or_null(params.get("account")),
            )
            typed_value = params.get("message", params.get("typedData"))
        else:
            first = params[0] if len(params) > 0 else None
            second = params[1] if len(params) > 1 else None
            if _looks_like_eth_address(first):
                address = _primitive_content_or_null(first)
                typed_value = second
            else:
                typed_value = first
                address = _primitive_content_or_null(second)
        typed_data_json = _extract_typed_data_json(typed_value)
        chain_id = (
            _json_rpc_chain_id(data, params)
            or _typed_data_domain_chain_id(typed_data_json)
            or 1
        )
        normalized_address = normalize_eth_address(address) if address else None
        tp_request = _json_rpc_tp_request(
            payload,
            "signTypedData_v4",
            "typed_data",
            chain_id,
            request_id,
            origin,
            normalized_address,
            typed_data_json=typed_data_json,
        )
        return Web3Request(
            source_format="json-rpc",
            data_type=Web3RequestDataType.TYPED_DATA,
            chain_id=chain_id,
            derivation_path=derivation_path,
            address=normalized_address,
            origin=origin,
            request_id_value=request_id,
            request_id_text=request_id,
            sign_data=typed_data_json.encode("utf-8"),
            raw_payload=payload,
            typed_data_json=typed_data_json,
            tp_request=tp_request,
        )

    raise Web3Error("当前仅支持 signTransaction / personalSign / signTypedData")


def parse_ur_eth_sign_request(ur: UR, raw_payload: Optional[str] = None) -> Web3Request:
    if ur.type.lower() != "eth-sign-request":
        raise Web3Error("当前只支持 eth-sign-request")
    root = _decode_cbor_map(bytes(ur.cbor))

    request_id_value = root.get(1)
    request_id_text = _parse_request_id_text(request_id_value)
    sign_data = bytes(root.get(2) or b"")
    data_type = Web3RequestDataType.from_code(int(root.get(3) or Web3RequestDataType.PERSONAL_MESSAGE))
    chain_id = int(root.get(4) or 1)
    derivation_path = _normalize_path(_extract_path_from_keypath(root.get(5)))
    address_value = root.get(6)
    address = None
    if address_value is not None:
        if isinstance(address_value, (bytes, bytearray)):
            address = normalize_eth_address(ethereum_address_from_bytes(bytes(address_value)))
        else:
            address = normalize_eth_address(str(address_value))
    origin = _primitive_content_or_null(root.get(7))
    message_text = None
    typed_data_json = None
    if data_type == Web3RequestDataType.PERSONAL_MESSAGE:
        message_text = _maybe_text(sign_data)
    elif data_type == Web3RequestDataType.TYPED_DATA:
        typed_data_json = _maybe_text(sign_data)
    return Web3Request(
        source_format="ur",
        data_type=data_type,
        chain_id=chain_id,
        derivation_path=derivation_path,
        address=address,
        origin=origin,
        request_id_value=request_id_value,
        request_id_text=request_id_text,
        sign_data=sign_data,
        raw_payload=raw_payload or "ur:{}".format(ur.type),
        message_text=message_text,
        typed_data_json=typed_data_json,
        tp_request=None,
    )


def parse_web3_request(payload: Any, qr_format: Optional[int] = None) -> Web3Request:
    if isinstance(payload, UR):
        return parse_ur_eth_sign_request(payload)

    if isinstance(payload, (bytes, bytearray)):
        text = bytes(payload).decode("utf-8", errors="ignore")
    else:
        text = str(payload)
    normalized = text.strip()

    if _starts_with_any(normalized.lower(), (RELAY_TP_PREFIX, RELAY_WEB3_PREFIX)):
        relay_prefix, relay_text = decode_relay_payload(normalized)
        if relay_prefix == RELAY_TP_PREFIX:
            tp_request = parse_tp_request(relay_text)
            return _tp_request_to_web3_request(
                tp_request,
                relay_text,
                source_format="tpr1",
            )
        relay = parse_web3_relay_envelope(relay_text)
        return _relay_envelope_to_web3_request(relay, relay_text)

    if qr_format is not None and qr_format == 4:
        tp_request = parse_tp_request(normalized)
        return _tp_request_to_web3_request(tp_request, normalized)
    if normalized.lower().startswith("ur:"):
        return parse_ur_eth_sign_request(URDecoder.decode(normalized), normalized)
    if normalized.lower().startswith("tp:"):
        if normalized.lower().startswith("tp:multifragment-"):
            raise Web3Error("tp:multifragment 需要先完成分片拼接")
        tp_request = parse_tp_request(normalized)
        return _tp_request_to_web3_request(tp_request, normalized)
    if normalized.startswith("{"):
        try:
            relay = parse_web3_relay_envelope(normalized)
            return _relay_envelope_to_web3_request(relay, normalized)
        except Web3Error as relay_error:
            try:
                return parse_json_rpc_web3_request(normalized)
            except Web3Error as json_error:
                if "JSON-RPC" in str(json_error):
                    raise json_error
                raise relay_error

    if qr_format is not None and qr_format == 2:
        return parse_ur_eth_sign_request(URDecoder.decode(normalized), normalized)

    raise Web3Error("无法识别的链上请求")


def params_to_path(tp_request: TpParsedRequest) -> str:
    if tp_request.kind in {"transaction", "typed_transaction"} and tp_request.tx_data:
        path = _primitive_content_or_null(tp_request.tx_data.get("path"))
        if path:
            return path
    return DEFAULT_EVM_ADDRESS_PATH


def _tp_request_to_web3_request(
    tp_request: TpParsedRequest,
    raw_payload: str,
    source_format: str = "tp",
    relay_envelope: Optional[Web3RelayEnvelope] = None,
) -> Web3Request:
    data_type = (
        Web3RequestDataType.TRANSACTION
        if tp_request.kind == "transaction"
        else Web3RequestDataType.TYPED_TRANSACTION
        if tp_request.kind == "typed_transaction"
        else Web3RequestDataType.PERSONAL_MESSAGE
        if tp_request.kind == "personal_message"
        else Web3RequestDataType.TYPED_DATA
    )
    sign_data = (
        decode_personal_message(tp_request.message or "")
        if tp_request.kind == "personal_message"
        else tp_request.typed_data_json.encode("utf-8")
        if tp_request.kind == "typed_data" and tp_request.typed_data_json
        else _json_dumps_compact(tp_request.tx_data or {}).encode("utf-8")
    )
    return Web3Request(
        source_format=source_format,
        data_type=data_type,
        chain_id=tp_request.chain_id,
        derivation_path=_normalize_path(params_to_path(tp_request)),
        address=tp_request.address,
        origin=tp_request.dapp_source
        or tp_request.dapp_name
        or tp_request.protocol
        or (relay_envelope.origin if relay_envelope else None)
        or (relay_envelope.wallet_name if relay_envelope else None),
        request_id_value=tp_request.request_id,
        request_id_text=tp_request.request_id,
        sign_data=sign_data,
        raw_payload=raw_payload,
        message_text=tp_request.message,
        typed_data_json=tp_request.typed_data_json,
        tp_request=tp_request,
        relay_wallet_name=relay_envelope.wallet_name if relay_envelope else None,
        relay_format=relay_envelope.detected_format if relay_envelope else None,
        relay_qr_type=relay_envelope.qr_type if relay_envelope else None,
        relay_chain_hint=relay_envelope.chain if relay_envelope else None,
    )


def _relay_envelope_to_web3_request(
    relay_envelope: Web3RelayEnvelope,
    raw_payload: str,
) -> Web3Request:
    inner_payload = relay_envelope.payload.strip()
    if not inner_payload:
        raise Web3Error("链上中转包缺少内部载荷")

    if inner_payload.lower().startswith("tp:"):
        tp_request = parse_tp_request(inner_payload)
        request = _tp_request_to_web3_request(
            tp_request,
            inner_payload,
            source_format="w3r1",
            relay_envelope=relay_envelope,
        )
    else:
        request = parse_web3_request(inner_payload)
        request.source_format = "w3r1"
        request.relay_wallet_name = relay_envelope.wallet_name
        request.relay_format = relay_envelope.detected_format
        request.relay_qr_type = relay_envelope.qr_type
        request.relay_chain_hint = relay_envelope.chain
        if not request.origin:
            request.origin = relay_envelope.origin or relay_envelope.wallet_name

    if relay_envelope.address_path:
        request.derivation_path = _normalize_path(relay_envelope.address_path, request.derivation_path)

    if relay_envelope.address:
        request.address = relay_envelope.address

    if relay_envelope.chain_id is not None:
        request.chain_id = relay_envelope.chain_id

    request.raw_payload = raw_payload
    return request


def build_tp_signature_response(request: TpParsedRequest, signature_hex: str, signer_address: str) -> str:
    if request.kind in {"transaction", "typed_transaction"}:
        response_data_obj = {"rawTransaction": signature_hex}
        response_id = request.action_id or request.data_id
        if response_id:
            response_data_obj["id"] = response_id
        response_data = _json_dumps_compact(response_data_obj)
    else:
        response_data = _json_dumps_compact(
            {"signature": signature_hex, "address": signer_address}
        )

    response_action = "{}Signature".format(request.action)
    if request.request_format == "legacy":
        query = _build_query(
            [
                ("v", request.version),
                ("requestId", request.request_id),
                ("action", request.action),
                ("actionId", request.action_id or request.data_id),
                ("data", response_data),
            ]
        )
        return "{}:{}-?{}".format(request.namespace, response_action, query)

    query = _build_query(
        [
            ("version", request.version),
            ("protocol", request.protocol),
            ("network", request.network),
            ("chain_id", str(request.chain_id)),
            ("requestId", request.request_id),
            ("data", response_data),
        ]
    )
    return "{}:{}-{}".format(request.namespace, response_action, query)


def _build_query(values: Sequence[Tuple[str, Optional[str]]]) -> str:
    pieces = []
    for key, value in values:
        if value is None:
            continue
        text = str(value)
        if not text.strip():
            continue
        pieces.append("{}={}".format(key, text))
    return "&".join(pieces)


def build_tp_multi_fragment_request(raw: str) -> Tuple[bool, Optional[TpMultiFragment]]:
    try:
        return True, parse_tp_multi_fragment(raw)
    except Exception:
        return False, None


# -----------------------------
# UR / QR bundle builders
# -----------------------------


def _ur_pages(
    ur: UR,
    max_fragment_len: int,
    first_seq_num: int = 0,
    redundancy_rounds: int = 2,
) -> List[str]:
    encoder = UREncoder(ur, max_fragment_len, first_seq_num)
    if encoder.is_single_part():
        return [UREncoder.encode(ur).upper()]

    pages = []
    seq_len = encoder.fountain_encoder.seq_len()
    for _ in range(seq_len * max(1, redundancy_rounds)):
        pages.append(encoder.next_part().upper())
    return pages


def _normalize_wallet_profile(value: Optional[str]) -> str:
    normalized = str(value or WEB3_WALLET_PROFILE_METAMASK).strip().lower()
    compact = normalized.replace("-", "").replace("_", "").replace(" ", "")
    if normalized in {"bitget", "bitkeep"}:
        return WEB3_WALLET_PROFILE_BITGET
    if compact == WEB3_WALLET_PROFILE_METAMASK:
        return WEB3_WALLET_PROFILE_METAMASK
    if compact == WEB3_WALLET_PROFILE_RABBY:
        return WEB3_WALLET_PROFILE_RABBY
    if compact in {WEB3_WALLET_PROFILE_TOKENPOCKET, "tpwallet", "tp"}:
        return WEB3_WALLET_PROFILE_TOKENPOCKET
    return WEB3_WALLET_PROFILE_OKX


def _path_parent(path: str) -> str:
    normalized = _normalize_path(path, path)
    if normalized == "m":
        return "m"
    pieces = normalized.split("/")
    if len(pieces) <= 1:
        return "m"
    return "/".join(pieces[:-1]) or "m"


def _pubkey_fingerprint(pubkey_sec: bytes) -> bytes:
    return hashes.hash160(pubkey_sec)[:4]


def _device_serial_from_account(account: Web3AccountInfo) -> str:
    return "tp-keystone-{}-{}".format(
        account.master_fingerprint_hex.lower(),
        account.address.lower(),
    )


def _web3_device_id(account: Web3AccountInfo, wallet_profile: str) -> str:
    profile = _normalize_wallet_profile(wallet_profile)
    serial = _device_serial_from_account(account)
    if profile == WEB3_WALLET_PROFILE_OKX:
        serial = "keystone{}".format(serial)
        return _sha256_hex(_sha256(serial.encode("utf-8")))[:40]
    return _bytes_hex(_sha256(_sha256(serial.encode("utf-8")))[:20])


def _web3_keypath(path: str, source_fingerprint: Optional[bytes], depth: Optional[int], allow_wildcard: bool = False) -> Keypath:
    return _keypath_from_components(
        path,
        source_fingerprint=source_fingerprint,
        depth=depth,
        allow_wildcard=allow_wildcard,
    )


def _web3_hdkey_entry(
    *,
    pubkey_sec: bytes,
    chain_code: Optional[bytes],
    origin_path: str,
    master_fingerprint: Optional[bytes],
    include_children: bool,
    children_path: Optional[str] = None,
    parent_fingerprint: Optional[bytes] = None,
    coin_type: Optional[int] = None,
    network: Optional[int] = None,
    note: str = "",
    name: str = "Keystone",
) -> HDKey:
    props = {
        "key": pubkey_sec,
        "origin": _web3_keypath(
            origin_path,
            source_fingerprint=master_fingerprint,
            depth=len(_parse_path_components(origin_path)),
        ),
        "name": name,
        "note": note,
    }
    if chain_code:
        props["chain_code"] = chain_code
    if coin_type is not None:
        props["use_info"] = CoinInfo(coin_type, network if network is not None else WEB3_MAINNET_NETWORK)
    if include_children and children_path:
        props["children"] = _web3_keypath(
            children_path,
            source_fingerprint=None,
            depth=0 if "*" in children_path else None,
            allow_wildcard=True,
        )
    if parent_fingerprint:
        props["parent_fingerprint"] = parent_fingerprint
    return HDKey(props)


def _build_multi_accounts_bundle(account: Web3AccountInfo, wallet_profile: str) -> Web3QrBundle:
    root = getattr(account, "_root", None)
    if root is None:
        raise Web3Error("当前钱包没有可用于链上功能的根密钥")

    profile = _normalize_wallet_profile(wallet_profile)
    master_fingerprint = account.master_fingerprint or b"\x00\x00\x00\x00"
    parent_pub = root.derive(bip32.parse_path(_path_parent(account.account_path))).to_public().sec()
    key_items = []
    key_items.append(
            DataItem(
                HDKey.registry_type().tag,
                _web3_hdkey_entry(
                    pubkey_sec=_bytes_from_hex(account.compressed_pubkey_hex),
                    chain_code=_bytes_from_hex(account.chain_code_hex),
                origin_path=account.account_path,
                master_fingerprint=master_fingerprint,
                include_children=True,
                children_path=account.children_path,
                parent_fingerprint=_pubkey_fingerprint(parent_pub),
                coin_type=WEB3_ETH_COIN_TYPE,
                network=WEB3_MAINNET_NETWORK,
                note="account.standard",
            ).to_data_item(),
        )
    )

    btc_paths = WEB3_BITGET_BTC_ACCOUNT_PATHS if profile == WEB3_WALLET_PROFILE_BITGET else WEB3_OKX_BTC_ACCOUNT_PATHS
    for account_path in btc_paths:
        derived = root.derive(bip32.parse_path(account_path))
        btc_parent = root.derive(bip32.parse_path(_path_parent(account_path))).to_public().sec()
        key_items.append(
            DataItem(
                HDKey.registry_type().tag,
                _web3_hdkey_entry(
                    pubkey_sec=derived.to_public().sec(),
                    chain_code=derived.chain_code,
                    origin_path=account_path,
                    master_fingerprint=master_fingerprint,
                    include_children=False,
                    parent_fingerprint=_pubkey_fingerprint(btc_parent),
                    coin_type=WEB3_BTC_COIN_TYPE,
                    network=WEB3_MAINNET_NETWORK,
                    note="",
                ).to_data_item(),
            )
        )

    if profile == WEB3_WALLET_PROFILE_OKX:
        for index in range(WEB3_OKX_LEDGER_LIVE_ACCOUNT_COUNT):
            ledger_path = "m/44'/60'/{}'/0/0".format(index)
            derived = root.derive(bip32.parse_path(ledger_path))
            key_items.append(
                DataItem(
                    HDKey.registry_type().tag,
                    _web3_hdkey_entry(
                        pubkey_sec=derived.to_public().sec(),
                        chain_code=None,
                        origin_path=ledger_path,
                        master_fingerprint=master_fingerprint,
                        include_children=False,
                        coin_type=WEB3_ETH_COIN_TYPE,
                        network=WEB3_MAINNET_NETWORK,
                        note="account.ledger_live",
                    ).to_data_item(),
                )
            )

    if profile == WEB3_WALLET_PROFILE_BITGET:
        cbor = _encode_cbor(
            {
                1: int(_bytes_hex(master_fingerprint), 16),
                2: key_items,
                3: WEB3_KEYSTONE_DEVICE_TYPE,
            }
        )
        ur = UR("crypto-multi-accounts", cbor)
        return Web3QrBundle(ur=ur, pages=[UREncoder.encode(ur).upper()])

    cbor = _encode_cbor(
        {
            1: int(_bytes_hex(master_fingerprint), 16),
            2: key_items,
            3: WEB3_OKX_DEVICE_TYPE,
            4: _web3_device_id(account, profile),
            5: WEB3_KEYSTONE_DEVICE_VERSION,
        }
    )
    ur = UR("crypto-multi-accounts", bytearray(cbor))
    return Web3QrBundle(ur=ur, pages=_ur_pages(ur, WEB3_OKX_CONNECT_QR_MAX_FRAGMENT_LEN))


def build_connect_qr_bundle(
    wallet_key: Any,
    account_path: str = DEFAULT_EVM_ACCOUNT_PATH,
    wallet_profile: str = WEB3_WALLET_PROFILE_METAMASK,
) -> Web3QrBundle:
    if wallet_key is None:
        raise Web3Error("请先加载助记词")
    root = getattr(wallet_key, "root", None)
    if root is None:
        raise Web3Error("当前钱包没有可用于链上功能的根密钥")

    account_path = _normalize_path(account_path, DEFAULT_EVM_ACCOUNT_PATH)
    profile = _normalize_wallet_profile(wallet_profile)
    address_path = _normalize_path("{}/0/0".format(account_path), DEFAULT_EVM_ADDRESS_PATH)
    account_hdkey = root.derive(bip32.parse_path(account_path))
    address_hdkey = root.derive(bip32.parse_path(address_path))
    address_pubkey = address_hdkey.to_public().get_public_key()
    uncompressed_pubkey = public_key_to_uncompressed_bytes(address_pubkey)
    address = ethereum_address_from_pubkey(uncompressed_pubkey)
    display_address = ethereum_checksum_address(address)

    master_fingerprint = root.my_fingerprint
    origin_keypath = _keypath(account_path, source_fingerprint=master_fingerprint, depth=len(_parse_path_components(account_path)))
    children_keypath = _keypath_from_components(DEFAULT_EVM_CHILDREN_PATH, depth=None, allow_wildcard=True)

    account = Web3AccountInfo(
        account_path=account_path,
        address_path=address_path,
        children_path=DEFAULT_EVM_CHILDREN_PATH,
        address=address,
        display_address=display_address,
        master_fingerprint=master_fingerprint,
        master_fingerprint_hex=_bytes_hex(master_fingerprint),
        compressed_pubkey_hex=_bytes_hex(account_hdkey.to_public().sec()),
        chain_code_hex=_bytes_hex(account_hdkey.chain_code),
        xpub=account_hdkey.to_public().to_base58(),
        origin_keypath=origin_keypath,
        children_keypath=children_keypath,
    )
    setattr(account, "_root", root)

    if profile in {WEB3_WALLET_PROFILE_OKX, WEB3_WALLET_PROFILE_BITGET}:
        return _build_multi_accounts_bundle(account, profile)

    if profile == WEB3_WALLET_PROFILE_TOKENPOCKET:
        return Web3QrBundle(ur=None, pages=[display_address], text=display_address)

    hdkey = HDKey(
        {
            "key": account_hdkey.to_public().sec(),
            "chain_code": account_hdkey.chain_code,
            "use_info": CoinInfo(WEB3_ETH_COIN_TYPE, WEB3_MAINNET_NETWORK),
            "origin": origin_keypath,
            "children": children_keypath,
            "name": "Krux",
            "note": "account.standard",
        }
    )
    ur = UR("crypto-hdkey", bytes(hdkey.to_cbor()))
    return Web3QrBundle(ur=ur, pages=_ur_pages(ur, 120))


def build_eth_signature_qr_bundle(
    request: Web3Request,
    signature_bytes: bytes,
    origin: Optional[str] = None,
) -> Web3QrBundle:
    if len(signature_bytes) != 65:
        raise Web3Error("签名结果长度不正确")
    map_data = {}
    if request.request_id_value is not None:
        map_data[1] = request.request_id_value
    elif request.request_id_text:
        map_data[1] = request.request_id_text
    else:
        map_data[1] = _fallback_request_id(signature_bytes)
    map_data[2] = signature_bytes
    if origin and origin.strip():
        map_data[3] = origin.strip()
    ur = UR("eth-signature", _encode_cbor(map_data))
    return Web3QrBundle(ur=ur, pages=_ur_pages(ur, 260))


def _fallback_request_id(seed: bytes) -> str:
    digest = _sha256_hex(seed)
    return "{}-{}-{}-{}-{}".format(
        digest[:8],
        digest[8:12],
        digest[12:16],
        digest[16:20],
        digest[20:32],
    )


def build_request_summary(request: Web3Request) -> str:
    origin = request.origin or ("TP" if request.source_format in {"tp", "tpr1"} else "UR")
    address = request.address
    if address:
        try:
            address = ethereum_checksum_address(address)
        except Exception:
            pass
    lines = [
        "来源: {}".format(origin),
        "类型: {}".format(_web3_request_type_label(request.data_type)),
        "链 ID: {}".format(request.chain_id),
        "路径: {}".format(request.derivation_path),
    ]
    if request.relay_wallet_name:
        lines.append("中转: {}".format(request.relay_wallet_name))
    if address:
        lines.append("地址: {}".format(_shorten_middle(address)))
    if request.request_id_text:
        lines.append("请求 ID: {}".format(request.request_id_text))
    if request.data_type in (
        Web3RequestDataType.TRANSACTION,
        Web3RequestDataType.TYPED_TRANSACTION,
    ):
        try:
            tx = _parse_web3_transaction_request(request)
            to_text = (
                "合约创建"
                if tx.to is None
                else _shorten_middle(_ensure_hex_prefix(_bytes_hex(tx.to)))
            )
            lines.extend(
                [
                    "交易: {}".format(_transaction_type_label(tx.tx_type)),
                    "收款: {}".format(to_text),
                    "金额(wei): {}".format(tx.value),
                    "序号: {}  Gas 限额: {}".format(tx.nonce, tx.gas_limit),
                ]
            )
            if tx.tx_type in (0, 1):
                lines.append("Gas 价格: {}".format(tx.gas_price))
            elif tx.tx_type == 2:
                lines.append(
                    "优先费: {}  上限: {}".format(
                        tx.max_priority_fee_per_gas,
                        tx.max_fee_per_gas,
                    )
                )
        except Web3Error as exc:
            lines.append("交易摘要: {}".format(exc))
    return "\n".join(lines)


def build_connect_summary(account: Web3AccountInfo, wallet_profile: str = WEB3_WALLET_PROFILE_METAMASK) -> str:
    profile = _normalize_wallet_profile(wallet_profile)
    wallet_name = WEB3_WALLET_PROFILE_LABELS.get(profile, "链上钱包")
    connect_mode = (
        "多账户"
        if profile in {WEB3_WALLET_PROFILE_OKX, WEB3_WALLET_PROFILE_BITGET}
        else "地址导入"
        if profile == WEB3_WALLET_PROFILE_TOKENPOCKET
        else "单账户"
    )
    return "\n".join(
        [
            "钱包: {}".format(wallet_name),
            "连接: {}".format(connect_mode),
            "地址: {}".format(_shorten_middle(account.display_address)),
            "路径: {}".format(account.address_path),
        ]
    )


def _wallet_root_for_web3(wallet_key: Any):
    if wallet_key is None:
        raise Web3Error("请先加载助记词")
    root = getattr(wallet_key, "root", None)
    if root is None:
        raise Web3Error("当前钱包没有可用于链上功能的根密钥")
    return root


def _derive_web3_address_from_root(root, address_path: str) -> str:
    address_hdkey = root.derive(bip32.parse_path(address_path))
    address_pubkey = address_hdkey.to_public().get_public_key()
    uncompressed_pubkey = public_key_to_uncompressed_bytes(address_pubkey)
    return ethereum_address_from_pubkey(uncompressed_pubkey)


def derive_web3_address(
    wallet_key: Any,
    address_path: str = DEFAULT_EVM_ADDRESS_PATH,
    checksum: bool = True,
) -> str:
    """Derive an EVM address from the exact full address path."""
    root = _wallet_root_for_web3(wallet_key)
    normalized_path = _normalize_path(address_path, DEFAULT_EVM_ADDRESS_PATH)
    address = _derive_web3_address_from_root(root, normalized_path)
    if checksum:
        return ethereum_checksum_address(address)
    return address


def derive_web3_account(wallet_key: Any, account_path: str = DEFAULT_EVM_ACCOUNT_PATH) -> Web3AccountInfo:
    root = _wallet_root_for_web3(wallet_key)

    account_path = _normalize_path(account_path, DEFAULT_EVM_ACCOUNT_PATH)
    address_path = _normalize_path("{}/0/0".format(account_path), DEFAULT_EVM_ADDRESS_PATH)
    account_hdkey = root.derive(bip32.parse_path(account_path))
    address = _derive_web3_address_from_root(root, address_path)
    display_address = ethereum_checksum_address(address)
    master_fingerprint = root.my_fingerprint
    origin_keypath = _keypath(
        account_path,
        source_fingerprint=master_fingerprint,
        depth=len(_parse_path_components(account_path)),
    )
    children_keypath = _keypath_from_components(
        DEFAULT_EVM_CHILDREN_PATH,
        depth=None,
        allow_wildcard=True,
    )
    return Web3AccountInfo(
        account_path=account_path,
        address_path=address_path,
        children_path=DEFAULT_EVM_CHILDREN_PATH,
        address=address,
        display_address=display_address,
        master_fingerprint=master_fingerprint,
        master_fingerprint_hex=_bytes_hex(master_fingerprint),
        compressed_pubkey_hex=_bytes_hex(account_hdkey.to_public().sec()),
        chain_code_hex=_bytes_hex(account_hdkey.chain_code),
        xpub=account_hdkey.to_public().to_base58(),
        origin_keypath=origin_keypath,
        children_keypath=children_keypath,
    )


def _build_synthetic_tp_transaction_request(request: Web3Request) -> TpParsedRequest:
    kind = "typed_transaction" if request.data_type == Web3RequestDataType.TYPED_TRANSACTION else "transaction"
    return TpParsedRequest(
        raw_payload=request.raw_payload,
        namespace="tp",
        action="signTransaction",
        request_format="modern",
        version="1.0",
        protocol="ArbitrumWallet",
        network="ethereum",
        chain_id=request.chain_id,
        request_id=request.request_id_text,
        action_id=request.request_id_text,
        data_id=request.request_id_text,
        dapp_name=None,
        dapp_url=None,
        dapp_source=request.origin,
        address=request.address,
        kind=kind,
        message=None,
        typed_data_json=None,
        tx_data=None,
    )


def _parse_web3_transaction_request(request: Web3Request) -> EvmUnsignedTransaction:
    if request.data_type not in (
        Web3RequestDataType.TRANSACTION,
        Web3RequestDataType.TYPED_TRANSACTION,
    ):
        raise Web3Error("当前请求不是交易类型")

    if request.tp_request is not None:
        if request.tp_request is None or not isinstance(request.tp_request.tx_data, dict):
            raise Web3Error("TP 交易请求缺少 txData")
        return _parse_tp_transaction_request(request.tp_request.tx_data, request.chain_id)

    return _parse_unsigned_transaction_bytes(request.sign_data, request.data_type, request.chain_id)


def sign_web3_request(wallet_key: Any, request: Web3Request) -> Web3SigningResult:
    if wallet_key is None:
        raise Web3Error("请先加载助记词")
    root = getattr(wallet_key, "root", None)
    if root is None:
        raise Web3Error("当前钱包没有可用于链上功能的根密钥")

    derivation_path = _normalize_path(request.derivation_path, DEFAULT_EVM_ADDRESS_PATH)
    derived_address = derive_web3_address(
        wallet_key,
        derivation_path,
        checksum=False,
    )
    if request.address and normalize_eth_address(request.address) != normalize_eth_address(derived_address):
        raise Web3Error("请求地址与当前派生地址不一致")

    unsigned_tx = None
    if request.data_type == Web3RequestDataType.PERSONAL_MESSAGE:
        digest = personal_sign_hash(request.sign_data)
    elif request.data_type == Web3RequestDataType.TYPED_DATA:
        typed_json = request.typed_data_json
        if not typed_json:
            try:
                typed_json = request.sign_data.decode("utf-8")
            except Exception:
                raise Web3Error("typedData 不是合法 UTF-8")
        digest = typed_data_hash(typed_json)
    else:
        unsigned_tx = _parse_web3_transaction_request(request)
        digest = keccak256(_encode_unsigned_transaction(unsigned_tx))

    rec_id, r, s = sign_digest_at_path(root, derivation_path, digest)
    signature_bytes = build_eth_signature_bytes(rec_id, r, s)
    if request.data_type in (
        Web3RequestDataType.TRANSACTION,
        Web3RequestDataType.TYPED_TRANSACTION,
    ):
        if unsigned_tx is None:
            unsigned_tx = _parse_web3_transaction_request(request)
        raw_tx = _encode_signed_transaction(
            unsigned_tx,
            rec_id,
            r,
            s,
        )
        signature_hex = _ensure_hex_prefix(_bytes_hex(raw_tx))
    else:
        signature_hex = build_eth_message_signature_hex(rec_id, r, s)

    if request.data_type in (
        Web3RequestDataType.TRANSACTION,
        Web3RequestDataType.TYPED_TRANSACTION,
    ):
        tp_request = request.tp_request or _build_synthetic_tp_transaction_request(request)
        response = build_tp_signature_response(tp_request, signature_hex, derived_address)
        qr_bundle = Web3QrBundle(ur=None, pages=[response], text=response)
    elif request.source_format == "ur":
        qr_bundle = build_eth_signature_qr_bundle(request, signature_bytes, origin=request.origin)
    else:
        if request.tp_request is None:
            raise Web3Error("TP 请求上下文缺失")
        response = build_tp_signature_response(request.tp_request, signature_hex, derived_address)
        qr_bundle = Web3QrBundle(ur=None, pages=[response], text=response)

    return Web3SigningResult(
        request=request,
        signer_address=derived_address,
        digest=digest,
        signature_bytes=signature_bytes,
        signature_hex=signature_hex,
        qr_bundle=qr_bundle,
    )


def parse_scanned_web3_request(payload: Any, qr_format: Optional[int] = None) -> Web3Request:
    if qr_format is not None and qr_format in (4, 5):
        return parse_web3_request(payload, qr_format)
    if isinstance(payload, UR):
        return parse_ur_eth_sign_request(payload)
    if isinstance(payload, (bytes, bytearray)):
        text = bytes(payload).decode("utf-8", errors="ignore")
    else:
        text = str(payload)
    normalized = text.strip()
    try:
        return parse_web3_request(normalized, qr_format)
    except Web3Error as first_error:
        decoded = _smart_decode(normalized).strip()
        if decoded and decoded != normalized:
            try:
                return parse_web3_request(decoded, qr_format)
            except Web3Error:
                pass
        raise first_error


# -----------------------------
# Public convenience helpers
# -----------------------------


def is_supported_web3_request(request: Web3Request) -> bool:
    return request.data_type in (
        Web3RequestDataType.TRANSACTION,
        Web3RequestDataType.TYPED_TRANSACTION,
        Web3RequestDataType.PERSONAL_MESSAGE,
        Web3RequestDataType.TYPED_DATA,
    )


def web3_request_type_label(data_type: Web3RequestDataType) -> str:
    return data_type.label()
