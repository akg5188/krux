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

from __future__ import annotations

import io
import hashlib
import json
import math
import re
import urllib.parse
import uuid
import zlib
from binascii import a2b_base64
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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


class Web3Error(ValueError):
    """Raised for malformed or unsupported Web3 payloads."""


class Web3RequestDataType(IntEnum):
    TRANSACTION = 1
    TYPED_DATA = 2
    PERSONAL_MESSAGE = 3
    TYPED_TRANSACTION = 4

    @classmethod
    def from_code(cls, code: int) -> "Web3RequestDataType":
        try:
            return cls(code)
        except Exception as exc:
            raise Web3Error(f"暂不支持的链上请求类型: {code}") from exc

    def label(self) -> str:
        if self == self.TRANSACTION:
            return "交易签名"
        if self == self.TYPED_DATA:
            return "结构化数据签名"
        if self == self.PERSONAL_MESSAGE:
            return "消息签名"
        return "结构化交易签名"


@dataclass
class TpParsedRequest:
    raw_payload: str
    namespace: str
    action: str
    request_format: str
    version: str
    protocol: str
    network: str
    chain_id: int
    request_id: Optional[str]
    action_id: Optional[str]
    data_id: Optional[str]
    dapp_name: Optional[str]
    dapp_url: Optional[str]
    dapp_source: Optional[str]
    address: Optional[str]
    kind: str
    message: Optional[str]
    typed_data_json: Optional[str]
    tx_data: Optional[Dict[str, Any]]


@dataclass
class Web3Request:
    source_format: str
    data_type: Web3RequestDataType
    chain_id: int
    derivation_path: str
    address: Optional[str]
    origin: Optional[str]
    request_id_value: Any
    request_id_text: Optional[str]
    sign_data: bytes
    raw_payload: str
    message_text: Optional[str] = None
    typed_data_json: Optional[str] = None
    tp_request: Optional[TpParsedRequest] = None
    relay_wallet_name: Optional[str] = None
    relay_format: Optional[str] = None
    relay_qr_type: Optional[str] = None
    relay_chain_hint: Optional[str] = None


@dataclass
class Web3QrBundle:
    ur: Optional[UR]
    pages: List[str]
    text: Optional[str] = None


@dataclass
class Web3AccountInfo:
    account_path: str
    address_path: str
    children_path: str
    address: str
    display_address: str
    master_fingerprint: bytes
    master_fingerprint_hex: str
    compressed_pubkey_hex: str
    chain_code_hex: str
    xpub: str
    origin_keypath: Keypath
    children_keypath: Keypath


@dataclass
class Web3SigningResult:
    request: Web3Request
    signer_address: str
    digest: bytes
    signature_bytes: bytes
    signature_hex: str
    qr_bundle: Web3QrBundle


@dataclass
class EvmAccessListEntry:
    address: bytes
    storage_keys: List[bytes]


@dataclass
class EvmUnsignedTransaction:
    tx_type: int
    chain_id: int
    nonce: int
    gas_limit: int
    to: Optional[bytes]
    value: int
    data: bytes
    gas_price: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    access_list: List[EvmAccessListEntry] = field(default_factory=list)


@dataclass
class TpMultiFragment:
    index: int
    total: int
    chunk: str
    crc32: str


@dataclass
class RelayFragment:
    prefix: str
    index: int
    total: int
    chunk: str
    crc32: str


@dataclass
class Web3RelayEnvelope:
    wallet: str
    wallet_name: str
    detected_format: Optional[str]
    qr_type: Optional[str]
    action: Optional[str]
    chain: Optional[str]
    payload: str
    response_protocol: Optional[str] = None
    request_id: Optional[str] = None
    origin: Optional[str] = None
    data_type_name: Optional[str] = None
    request_data_type_id: Optional[int] = None
    request_sign_data_hex: Optional[str] = None
    chain_id: Optional[int] = None
    address: Optional[str] = None
    address_path: Optional[str] = None
    expected_address: Optional[str] = None


class TpMultiFragmentAssembler:
    def __init__(self) -> None:
        self.expected_total: Optional[int] = None
        self.expected_crc: Optional[str] = None
        self.raw_fragments: Dict[int, str] = {}

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
            return "error", f"分片索引不合法 (index={index} total={total})"

        if self.expected_total is None:
            self.expected_total = total
            self.expected_crc = fragment.crc32
        elif self.expected_total != total or self.expected_crc != fragment.crc32:
            self.reset()
            return "error", "分片属于不同二维码序列，已重置"

        self.raw_fragments[index] = fragment.chunk

        expected = self.expected_total or total
        if self.received_count < expected:
            return "progress", f"已接收分片 {self.received_count}/{expected}"

        payload = self._assemble_payload(expected)
        if payload is None:
            self.reset()
            return "error", "分片索引基准不一致或有缺片"

        crc = str(zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF)
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
        self.expected_total: Optional[int] = None
        self.expected_crc: Optional[str] = None
        self.raw_fragments: Dict[int, str] = {}

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
            return "error", f"分片索引不合法 (index={index} total={total})"

        if self.expected_total is None:
            self.expected_total = total
            self.expected_crc = fragment.crc32
        elif self.expected_total != total or self.expected_crc != fragment.crc32:
            self.reset()
            return "error", "分片属于不同二维码序列，已重置"

        self.raw_fragments[index] = fragment.chunk

        expected = self.expected_total or total
        if self.received_count < expected:
            return "progress", f"已接收分片 {self.received_count}/{expected}"

        encoded = self._assemble_payload(expected)
        if encoded is None:
            self.reset()
            return "error", "分片索引基准不一致或有缺片"

        crc = str(zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF)
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


def _clean_hex_prefix(value: str) -> str:
    if value.startswith(("0x", "0X")):
        return value[2:]
    return value


def _ensure_hex_prefix(value: str) -> str:
    if value.startswith(("0x", "0X")):
        return value
    return f"0x{value}"


def _hex_to_bytes(value: Optional[str]) -> bytes:
    if value is None:
        return b""
    text = _clean_hex_prefix(value.strip())
    if not text:
        return b""
    if len(text) % 2:
        text = "0" + text
    try:
        return bytes.fromhex(text)
    except Exception as exc:
        raise Web3Error("Invalid hex string") from exc


def bytes_to_hex(data: bytes) -> str:
    return data.hex()


def normalize_eth_address(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    text = _ensure_hex_prefix(_clean_hex_prefix(text)).lower()
    if len(_clean_hex_prefix(text)) != 40:
        raise Web3Error(f"地址格式无效: {value}")
    return text


def _shorten_middle(value: str, prefix_len: int = 10, suffix_len: int = 8) -> str:
    if len(value) <= prefix_len + suffix_len + 3:
        return value
    return f"{value[:prefix_len]}...{value[-suffix_len:]}"


def ethereum_checksum_address(value: str) -> str:
    normalized = normalize_eth_address(value)
    if normalized is None:
        raise Web3Error("地址为空")
    clean = _clean_hex_prefix(normalized)
    digest = keccak256(clean.encode("ascii")).hex()
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
    return _ensure_hex_prefix(address_bytes.hex())


def ethereum_address_from_pubkey(pubkey_uncompressed: bytes) -> str:
    if len(pubkey_uncompressed) != 65 or pubkey_uncompressed[0] != 0x04:
        raise Web3Error("Expected uncompressed 65-byte public key")
    return _ensure_hex_prefix(keccak256(pubkey_uncompressed[1:])[-20:].hex())


def public_key_to_uncompressed_bytes(pubkey: ec.PublicKey) -> bytes:
    return ec.PublicKey(pubkey._point, compressed=False).sec()  # pylint: disable=protected-access


def decode_personal_message(message: str | bytes) -> bytes:
    if isinstance(message, (bytes, bytearray)):
        return bytes(message)
    if message.startswith(("0x", "0X")):
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
        return bytes(value).hex()
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
        return f"m/{path}"
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
        text = f"m/{text.lstrip('/')}"
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
    components: List[PathComponent] = []
    for part in parts:
        if allow_wildcard and part == "*":
            components.append(PathComponent(None, False))
            continue
        hardened = part.endswith(("'", "h", "H"))
        numeric = part[:-1] if hardened else part
        if not numeric.isdigit():
            raise Web3Error(f"派生路径片段无效: {part}")
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
    return re.findall(r"\[[^\]]*\]", type_name)


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
    deps: List[str] = []
    seen: set[str] = set()

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
        raise Web3Error(f"typedData 缺少类型定义: {primary_type}")
    parts = [
        f"{primary_type}(" + ",".join(
            f"{_field_type(field)} {_field_name(field)}" for field in types[primary_type]
        )
        + ")"
    ]
    for dependency in _dependencies(primary_type, types):
        parts.append(
            f"{dependency}("
            + ",".join(
                f"{_field_type(field)} {_field_name(field)}" for field in types[dependency]
            )
            + ")"
        )
    return "".join(parts)


def _infer_domain_types(domain: Dict[str, Any]) -> List[Dict[str, str]]:
    inferred: List[Dict[str, str]] = []
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
        if text.startswith(("0x", "0X")):
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
        if text.startswith(("0x", "0X")):
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
            raise Web3Error(f"不支持的 typedData 字段类型: {field_type}")
        size = int(size_text)
        if size < 1 or size > 32:
            raise Web3Error(f"不支持的 typedData 字段类型: {field_type}")
        raw = _coerce_bytes(value)
        if len(raw) > size:
            raise Web3Error(f"typedData 字段 {field_type} 过长")
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
    raise Web3Error(f"不支持的 typedData 字段类型: {field_type}")


def _encode_value(field_type: str, value: Any, types: Dict[str, List[Dict[str, Any]]]) -> bytes:
    dims = _array_dims(field_type)
    if dims:
        if not isinstance(value, (list, tuple)):
            raise Web3Error(f"typedData 数组字段格式无效: {field_type}")
        base_type = _base_type(field_type)
        fixed_length = dims[0][1:-1]
        if fixed_length and int(fixed_length) != len(value):
            raise Web3Error(f"typedData 数组长度不正确: {field_type}")
        encoded = b"".join(_encode_value(base_type + "".join(dims[1:]), item, types) for item in value)
        return keccak256(encoded)

    base_type = _base_type(field_type)
    if _is_struct_type(base_type, types):
        if not isinstance(value, dict):
            raise Web3Error(f"typedData 对象字段格式无效: {base_type}")
        return keccak256(_encode_data(base_type, value, types))
    return _encode_primitive(field_type, value)


def _encode_data(primary_type: str, data: Dict[str, Any], types: Dict[str, List[Dict[str, Any]]]) -> bytes:
    type_hash = keccak256(_encode_type(primary_type, types).encode("utf-8"))
    encoded = bytearray(type_hash)
    for field in types[primary_type]:
        name = _field_name(field)
        field_type = _field_type(field)
        if name not in data:
            raise Web3Error(f"typedData 缺少字段: {name}")
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
    except Exception as exc:
        raise Web3Error("typedData 解析失败: message 不是合法 JSON") from exc

    if not isinstance(typed_obj, dict):
        raise Web3Error("typedData 解析失败: 顶层必须是 JSON 对象")

    types_raw = typed_obj.get("types") or {}
    if not isinstance(types_raw, dict) or not types_raw:
        raise Web3Error("typedData 解析失败: 缺少 types")
    types: Dict[str, List[Dict[str, Any]]] = {
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
    raise Web3Error(f"非法 recovery id: {rec_id}")


def build_eth_signature_bytes(rec_id: int, r: int, s: int) -> bytes:
    normalized = _normalize_recovery_id(rec_id)
    return _int_to_fixed_bytes(r, 32) + _int_to_fixed_bytes(s, 32) + bytes([normalized])


def build_eth_message_signature_hex(rec_id: int, r: int, s: int) -> str:
    normalized = _normalize_recovery_id(rec_id)
    v = 27 + normalized
    signature = _int_to_fixed_bytes(r, 32) + _int_to_fixed_bytes(s, 32) + bytes([v & 0xFF])
    return _ensure_hex_prefix(signature.hex())


def _int_to_fixed_bytes(value: int, size: int) -> bytes:
    raw = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    if len(raw) > size and raw[0] == 0:
        raw = raw[1:]
    if len(raw) > size:
        raise Web3Error(f"Integer does not fit in {size} bytes")
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
    prefix = f"\x19Ethereum Signed Message:\n{len(message_bytes)}".encode("utf-8")
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
    values: List[Any] = []
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
    raise Web3Error(f"{label} 不是字节串")


def _rlp_require_list(value: Any, label: str) -> List[Any]:
    if isinstance(value, list):
        return value
    raise Web3Error(f"{label} 不是列表")


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
    except Exception as exc:
        raise Web3Error(f"{label} 格式无效") from exc


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
        except Exception as exc:
            raise Web3Error(f"{label} 不是合法十六进制") from exc
    raise Web3Error(f"{label} 格式无效")


def _parse_eth_address_bytes(value: Any, label: str) -> Optional[bytes]:
    text = _primitive_content_or_null(value)
    if text is None:
        return None
    normalized = normalize_eth_address(text)
    if normalized is None:
        return None
    try:
        raw = _hex_to_bytes(normalized)
    except Exception as exc:
        raise Web3Error(f"{label} 不是合法地址") from exc
    if len(raw) != 20:
        raise Web3Error(f"{label} 长度不正确")
    return raw


def _parse_access_list_json(value: Any) -> List[EvmAccessListEntry]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise Web3Error("accessList 格式无效")

    entries: List[EvmAccessListEntry] = []
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
    entries: List[EvmAccessListEntry] = []
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
        if text.startswith(("0x", "0X")):
            return int(text[2:] or "0", 16)
        return int(text, 10)
    raise Web3Error("交易 type 格式无效")


def _parse_tp_transaction_request(tx_data: Dict[str, Any], chain_id: int) -> EvmUnsignedTransaction:
    tx_type = _parse_tx_type(tx_data.get("type"))
    if tx_type not in (0, 1, 2):
        raise Web3Error(f"暂不支持的交易类型: {tx_type}")

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
        raise Web3Error(f"当前暂不支持的 typed transaction 类型: 0x{tx_type:02x}")

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

    raise Web3Error(f"暂不支持的交易类型: {tx.tx_type}")


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

    raise Web3Error(f"暂不支持的交易类型: {tx.tx_type}")


def _transaction_type_label(tx_type: int) -> str:
    if tx_type == 0:
        return "传统"
    if tx_type == 1:
        return "EIP-2930"
    if tx_type == 2:
        return "EIP-1559"
    return f"0x{tx_type:02x}"


# -----------------------------
# TP request parsing and responses
# -----------------------------


def normalize_action(action: str) -> str:
    return action.lower().translate({ord(char): None for char in "-_ " if char})


def _parse_optional_chain_id(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        value = text.split(":")[-1]
        if value.startswith(("0x", "0X")):
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
        if text.startswith(("0x", "0X")):
            return int(text[2:] or "0", 16)
        return int(text, 10)
    except Exception:
        return None


def _parse_query(query_raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
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
        return urllib.parse.unquote(value)
    except Exception:
        return value


def _extract_typed_data_json(message_element: Any) -> str:
    if isinstance(message_element, (dict, list)):
        text = json.dumps(message_element, ensure_ascii=False, separators=(",", ":"))
    elif isinstance(message_element, str):
        text = message_element.strip()
    else:
        raise Web3Error("typedData message 格式无效")

    if not (text.startswith("{") or text.startswith("[")):
        raise Web3Error("typedData message 必须是 JSON 字符串")

    try:
        json.loads(text)
    except Exception as exc:
        raise Web3Error("typedData message 不是合法 JSON") from exc
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

    query_raw = raw[dash + 1 :].removeprefix("?")
    params = _parse_query(query_raw)
    data_raw = params.get("data")
    if data_raw is None:
        raise Web3Error("缺少 data 字段")
    try:
        data_json = json.loads(data_raw)
    except Exception as exc:
        raise Web3Error("data JSON 无效") from exc
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
        raise Web3Error(f"分片 data JSON 无效: {exc}") from exc
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
    normalized = encoded.replace("-", "+").replace("_", "/")
    padding = len(normalized) % 4
    if padding:
        normalized += "=" * (4 - padding)
    try:
        return a2b_base64(normalized)
    except Exception as exc:
        raise Web3Error("中转二维码 Base64 解码失败") from exc


def _inflate_relay_text(encoded: str) -> str:
    compressed = _decode_relay_base64(encoded)
    try:
        raw = zlib.decompress(compressed)
    except Exception:
        try:
            raw = zlib.decompress(compressed, -15)
        except Exception as exc:
            raise Web3Error("中转二维码解压失败") from exc
    try:
        return raw.decode("utf-8")
    except Exception as exc:
        raise Web3Error("中转二维码文本解码失败") from exc


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
    except Exception as exc:
        raise Web3Error("中转分片序号无效") from exc

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
    except Exception as exc:
        raise Web3Error("链上中转包 JSON 无效") from exc
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
            raise Web3Error(f"暂不支持的交易类型: {tx_type}")
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
        return bytes(value).hex()
    return str(value)


def _first_non_blank(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value is not None and value.strip():
            return value.strip()
    return None


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
        raw_payload=raw_payload or f"ur:{ur.type}",
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

    if normalized.lower().startswith((RELAY_TP_PREFIX, RELAY_WEB3_PREFIX)):
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
        relay = parse_web3_relay_envelope(normalized)
        return _relay_envelope_to_web3_request(relay, normalized)

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
        else json.dumps(
            tp_request.tx_data or {}, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
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
        response_data_obj: Dict[str, Any] = {"rawTransaction": signature_hex}
        response_id = request.action_id or request.data_id
        if response_id:
            response_data_obj["id"] = response_id
        response_data = json.dumps(
            response_data_obj,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    else:
        response_data = json.dumps(
            {"signature": signature_hex, "address": signer_address},
            ensure_ascii=False,
            separators=(",", ":"),
        )

    response_action = f"{request.action}Signature"
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
        return f"{request.namespace}:{response_action}-?{query}"

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
    return f"{request.namespace}:{response_action}-{query}"


def _build_query(values: Sequence[Tuple[str, Optional[str]]]) -> str:
    pieces = []
    for key, value in values:
        if value is None:
            continue
        text = str(value)
        if not text.strip():
            continue
        pieces.append(f"{key}={text}")
    return "&".join(pieces)


def build_tp_multi_fragment_request(raw: str) -> Tuple[bool, Optional[TpMultiFragment]]:
    try:
        return True, parse_tp_multi_fragment(raw)
    except Exception:
        return False, None


# -----------------------------
# UR / QR bundle builders
# -----------------------------


def _ur_pages(ur: UR, max_fragment_len: int, first_seq_num: int = 10) -> List[str]:
    encoder = UREncoder(ur, max_fragment_len, first_seq_num)
    if encoder.is_single_part():
        return [UREncoder.encode(ur).upper()]

    pages: List[str] = []
    seq_len = encoder.fountain_encoder.seq_len()
    for _ in range(seq_len):
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
    return f"tp-keystone-{account.master_fingerprint_hex.lower()}-{account.address.lower()}"


def _web3_device_id(account: Web3AccountInfo, wallet_profile: str) -> str:
    profile = _normalize_wallet_profile(wallet_profile)
    serial = _device_serial_from_account(account)
    if profile == WEB3_WALLET_PROFILE_OKX:
        serial = f"keystone{serial}"
        return hashlib.sha256(hashlib.sha256(serial.encode("utf-8")).digest()).hexdigest()[:40]
    return hashlib.sha256(hashlib.sha256(serial.encode("utf-8")).digest()).digest()[:20].hex()


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
    props: Dict[str, Any] = {
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
    key_items: List[DataItem] = []
    key_items.append(
        DataItem(
            HDKey.registry_type().tag,
            _web3_hdkey_entry(
                pubkey_sec=bytes.fromhex(account.compressed_pubkey_hex),
                chain_code=bytes.fromhex(account.chain_code_hex),
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
            ledger_path = f"m/44'/60'/{index}'/0/0"
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
                1: int(master_fingerprint.hex(), 16),
                2: key_items,
                3: WEB3_KEYSTONE_DEVICE_TYPE,
            }
        )
        ur = UR("crypto-multi-accounts", cbor)
        return Web3QrBundle(ur=ur, pages=[UREncoder.encode(ur).upper()])

    cbor = _encode_cbor(
        {
            1: int(master_fingerprint.hex(), 16),
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
    address_path = _normalize_path(f"{account_path}/0/0", DEFAULT_EVM_ADDRESS_PATH)
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
        master_fingerprint_hex=master_fingerprint.hex(),
        compressed_pubkey_hex=account_hdkey.to_public().sec().hex(),
        chain_code_hex=account_hdkey.chain_code.hex(),
        xpub=account_hdkey.to_public().to_base58(),
        origin_keypath=origin_keypath,
        children_keypath=children_keypath,
    )
    setattr(account, "_root", root)

    if profile in {WEB3_WALLET_PROFILE_OKX, WEB3_WALLET_PROFILE_BITGET}:
        return _build_multi_accounts_bundle(account, profile)

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
    map_data: Dict[int, Any] = {}
    if request.request_id_value is not None:
        map_data[1] = request.request_id_value
    elif request.request_id_text:
        map_data[1] = request.request_id_text
    else:
        map_data[1] = str(uuid.uuid4())
    map_data[2] = signature_bytes
    if origin and origin.strip():
        map_data[3] = origin.strip()
    ur = UR("eth-signature", _encode_cbor(map_data))
    return Web3QrBundle(ur=ur, pages=_ur_pages(ur, 260))


def build_request_summary(request: Web3Request) -> str:
    origin = request.origin or ("TP" if request.source_format in {"tp", "tpr1"} else "UR")
    address = request.address
    if address:
        try:
            address = ethereum_checksum_address(address)
        except Exception:
            pass
    lines = [
        f"来源: {origin}",
        f"类型: {request.data_type.label()}",
        f"链 ID: {request.chain_id}",
        f"路径: {request.derivation_path}",
    ]
    if request.relay_wallet_name:
        lines.append(f"中转: {request.relay_wallet_name}")
    if address:
        lines.append(f"地址: {_shorten_middle(address)}")
    if request.request_id_text:
        lines.append(f"请求 ID: {request.request_id_text}")
    if request.data_type in (
        Web3RequestDataType.TRANSACTION,
        Web3RequestDataType.TYPED_TRANSACTION,
    ):
        try:
            tx = _parse_web3_transaction_request(request)
            to_text = "合约创建" if tx.to is None else _shorten_middle(_ensure_hex_prefix(tx.to.hex()))
            lines.extend(
                [
                    f"交易: {_transaction_type_label(tx.tx_type)}",
                    f"收款: {to_text}",
                    f"金额(wei): {tx.value}",
                    f"序号: {tx.nonce}  Gas 限额: {tx.gas_limit}",
                ]
            )
            if tx.tx_type in (0, 1):
                lines.append(f"Gas 价格: {tx.gas_price}")
            elif tx.tx_type == 2:
                lines.append(
                    f"优先费: {tx.max_priority_fee_per_gas}  上限: {tx.max_fee_per_gas}"
                )
        except Web3Error as exc:
            lines.append(f"交易摘要: {exc}")
    return "\n".join(lines)


def build_connect_summary(account: Web3AccountInfo, wallet_profile: str = WEB3_WALLET_PROFILE_METAMASK) -> str:
    profile = _normalize_wallet_profile(wallet_profile)
    wallet_name = WEB3_WALLET_PROFILE_LABELS.get(profile, "链上钱包")
    connect_mode = "多账户" if profile in {WEB3_WALLET_PROFILE_OKX, WEB3_WALLET_PROFILE_BITGET} else "单账户"
    return "\n".join(
        [
            f"钱包: {wallet_name}",
            f"连接: {connect_mode}",
            f"地址: {_shorten_middle(account.display_address)}",
            f"路径: {account.address_path}",
        ]
    )


def derive_web3_account(wallet_key: Any, account_path: str = DEFAULT_EVM_ACCOUNT_PATH) -> Web3AccountInfo:
    if wallet_key is None:
        raise Web3Error("请先加载助记词")
    root = getattr(wallet_key, "root", None)
    if root is None:
        raise Web3Error("当前钱包没有可用于链上功能的根密钥")

    account_path = _normalize_path(account_path, DEFAULT_EVM_ACCOUNT_PATH)
    address_path = _normalize_path(f"{account_path}/0/0", DEFAULT_EVM_ADDRESS_PATH)
    account_hdkey = root.derive(bip32.parse_path(account_path))
    address_hdkey = root.derive(bip32.parse_path(address_path))
    address_pubkey = address_hdkey.to_public().get_public_key()
    uncompressed_pubkey = public_key_to_uncompressed_bytes(address_pubkey)
    address = ethereum_address_from_pubkey(uncompressed_pubkey)
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
        master_fingerprint_hex=master_fingerprint.hex(),
        compressed_pubkey_hex=account_hdkey.to_public().sec().hex(),
        chain_code_hex=account_hdkey.chain_code.hex(),
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

    if request.source_format in {"tp", "tpr1", "w3r1"}:
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
    derived_address = derive_web3_account(wallet_key, derivation_path.rsplit("/", 2)[0]).address
    if request.address and normalize_eth_address(request.address) != normalize_eth_address(derived_address):
        raise Web3Error("请求地址与当前派生地址不一致")

    unsigned_tx: Optional[EvmUnsignedTransaction] = None
    if request.data_type == Web3RequestDataType.PERSONAL_MESSAGE:
        digest = personal_sign_hash(request.sign_data)
    elif request.data_type == Web3RequestDataType.TYPED_DATA:
        typed_json = request.typed_data_json
        if not typed_json:
            try:
                typed_json = request.sign_data.decode("utf-8")
            except Exception as exc:
                raise Web3Error("typedData 不是合法 UTF-8") from exc
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
        signature_hex = _ensure_hex_prefix(raw_tx.hex())
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
    if normalized.lower().startswith(("ur:", "tpr1:", "w3r1:")):
        return parse_web3_request(normalized)
    if normalized.lower().startswith("tp:"):
        if normalized.lower().startswith("tp:multifragment-"):
            raise Web3Error("tp:multifragment 需要先完成分片拼接")
        return parse_web3_request(normalized)
    raise Web3Error("无法识别的链上请求")


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
