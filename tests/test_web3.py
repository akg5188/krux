import base64
import gzip
import io
import json
import sys
import types
import urllib.parse
import zlib

import pytest


def make_wallet():
    from embit.networks import NETWORKS

    from krux.key import TYPE_SINGLESIG, Key
    from krux.wallet import Wallet

    mnemonic = (
        "abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon abandon about"
    )
    return Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"]))


def assert_display_ready_qr_bundle(bundle, expected_prefix=None):
    assert isinstance(bundle.pages, list)
    assert bundle.pages
    for page in bundle.pages:
        assert isinstance(page, str)
        assert page
        if expected_prefix is not None:
            assert page.startswith(expected_prefix)
    if bundle.text is not None:
        assert isinstance(bundle.text, str)


def test_web3_avoids_tuple_prefix_suffix_calls_for_micropython():
    from pathlib import Path

    source = Path(__file__).parents[1] / "src" / "krux" / "web3.py"
    text = source.read_text(encoding="utf-8")

    assert ".startswith((" not in text
    assert ".endswith((" not in text


def test_web3_json_dumps_compact_falls_back_for_micropython_ujson(monkeypatch):
    from krux import web3

    class MicroJson:
        def dumps(self, data, *args, **kwargs):
            if kwargs:
                raise TypeError("function doesn't take keyword arguments")
            return '{"ok":true}'

    monkeypatch.setattr(web3, "json", MicroJson())

    assert web3._json_dumps_compact({"ok": True}) == '{"ok":true}'


def build_tp_raw_request(action, data, request_id="req-1", legacy=False, chain_id="1"):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    query = [
        ("version", "1.0"),
        ("protocol", "ArbitrumWallet"),
        ("network", "ethereum"),
        ("chain_id", str(chain_id)),
        ("requestId", request_id),
        ("data", urllib.parse.quote(payload, safe="")),
    ]
    if legacy:
        query = [
            ("v", "1.0"),
            ("requestId", request_id),
            ("action", action),
            ("actionId", request_id),
            ("data", urllib.parse.quote(payload, safe="")),
        ]
        return f"tp:{action}-?" + "&".join(f"{key}={value}" for key, value in query)
    return f"tp:{action}-" + "&".join(f"{key}={value}" for key, value in query)


def build_ur_eth_sign_request(wallet, sign_data, request_id="req-1", data_type=3):
    from ur.ur import UR
    from urtypes.cbor import DataItem
    from urtypes.crypto import Keypath, PathComponent

    from krux.web3 import _encode_cbor, derive_web3_account

    address = derive_web3_account(wallet.key).address
    components = [
        PathComponent(44, True),
        PathComponent(60, True),
        PathComponent(0, True),
        PathComponent(0, False),
        PathComponent(0, False),
    ]
    keypath = Keypath(components, wallet.key.root.my_fingerprint, len(components))
    root_map = {
        1: request_id,
        2: sign_data,
        3: data_type,
        4: 1,
        5: DataItem(Keypath.registry_type().tag, keypath.to_data_item()),
        6: bytes.fromhex(address[2:]),
        7: "krux",
    }
    return UR("eth-sign-request", _encode_cbor(root_map))


def build_eip712_typed_data():
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Person": [
                {"name": "name", "type": "string"},
                {"name": "wallet", "type": "address"},
            ],
            "Mail": [
                {"name": "from", "type": "Person"},
                {"name": "to", "type": "Person"},
                {"name": "contents", "type": "string"},
            ],
        },
        "primaryType": "Mail",
        "domain": {
            "name": "Ether Mail",
            "version": "1",
            "chainId": 1,
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        "message": {
            "from": {
                "name": "Cow",
                "wallet": "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826",
            },
            "to": {
                "name": "Bob",
                "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
            },
            "contents": "Hello, Bob!",
        },
    }


def build_hyperliquid_spot_send_typed_data():
    return {
        "domain": {
            "name": "HyperliquidSignTransaction",
            "version": "1",
            "chainId": int("0x66eee", 16),
            "verifyingContract": "0x0000000000000000000000000000000000000000",
        },
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "HyperliquidTransaction:SpotSend": [
                {"name": "hyperliquidChain", "type": "string"},
                {"name": "destination", "type": "string"},
                {"name": "token", "type": "string"},
                {"name": "amount", "type": "string"},
                {"name": "time", "type": "uint64"},
            ],
        },
        "primaryType": "HyperliquidTransaction:SpotSend",
        "message": {
            "signatureChainId": "0x66eee",
            "hyperliquidChain": "Mainnet",
            "destination": "0x000000000000000000000000000000000000dEaD",
            "token": "USDC",
            "amount": "1.23",
            "time": 1700000000000,
        },
    }


def build_hyperliquid_l1_agent_typed_data():
    return {
        "domain": {
            "chainId": 1337,
            "name": "Exchange",
            "verifyingContract": "0x0000000000000000000000000000000000000000",
            "version": "1",
        },
        "types": {
            "Agent": [
                {"name": "source", "type": "string"},
                {"name": "connectionId", "type": "bytes32"},
            ],
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
        },
        "primaryType": "Agent",
        "message": {
            "source": "a",
            "connectionId": "0x1111111111111111111111111111111111111111111111111111111111111111",
        },
    }


def build_tp_multi_fragment_raw(payload, index, total, chunk):
    data = {
        "content": f"{chunk}_{zlib.crc32(payload.encode('utf-8')) & 0xFFFFFFFF}",
        "index": f"{index}/{total}",
        "total": total,
    }
    encoded = urllib.parse.quote(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), safe=""
    )
    return f"tp:multiFragment-?data={encoded}"


def build_compact_relay_pages(prefix, payload, chunk_chars=56):
    encoded = base64.urlsafe_b64encode(zlib.compress(payload.encode("utf-8"))).decode(
        "ascii"
    )
    encoded = encoded.rstrip("=")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    chunks = [encoded[i : i + chunk_chars] for i in range(0, len(encoded), chunk_chars)]
    return [
        f"{prefix}{index + 1}/{len(chunks)}.{crc}.{chunk}"
        for index, chunk in enumerate(chunks)
    ]


def build_tpr1_pages(payload, chunk_chars=56):
    return build_compact_relay_pages("tpr1:", payload, chunk_chars)


def build_w3r1_pages(inner_payload, chunk_chars=56):
    envelope = json.dumps(
        {
            "version": 1,
            "wallet": "OKX",
            "wallet_name": "OKX Wallet",
            "format": "Keystone / AirGap UR",
            "qr_type": "eth-sign-request",
            "action": "EVM 签名请求",
            "chain": "Ethereum/EVM",
            "payload": inner_payload,
            "response_protocol": "eth-signature",
            "request_id": "relay-req-1",
            "origin": "OKX Wallet",
            "chain_id": 1,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return build_compact_relay_pages("w3r1:", envelope, chunk_chars)


def _raw_deflate(data, wbits=-15):
    compressor = zlib.compressobj(wbits=wbits)
    return compressor.compress(data) + compressor.flush()


@pytest.mark.parametrize(
    "data, expected",
    [
        (b"", "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"),
        (
            b"ClickHouse",
            "e50bcd489117263eff31d66d4ac3862bc98c2a34795834d56ecb237daf88dc12",
        ),
        (
            b"Hello World",
            "592fa743889fc7f92ac2a37bb1f5ba1daf2a5c84741ca0e0061d243a2e6707ba",
        ),
    ],
)
def test_keccak256_vectors(data, expected):
    from krux.web3 import keccak256

    assert keccak256(data).hex() == expected


def test_keccak256_pure_python_vectors():
    from krux.web3 import _keccak256_pure_python

    assert (
        _keccak256_pure_python(b"ClickHouse").hex()
        == "e50bcd489117263eff31d66d4ac3862bc98c2a34795834d56ecb237daf88dc12"
    )


def test_build_connect_qr_bundle_roundtrip():
    from urtypes.crypto import HDKey

    from krux.web3 import build_connect_qr_bundle, derive_web3_account

    wallet = make_wallet()
    account = derive_web3_account(wallet.key)
    bundle = build_connect_qr_bundle(wallet.key)
    decoded = HDKey.from_cbor(bytes(bundle.ur.cbor))

    assert bundle.ur.type == "crypto-hdkey"
    assert bundle.pages
    assert bundle.pages[0].lower().startswith("ur:crypto-hdkey/")
    assert decoded.use_info.type == 0x3C
    assert decoded.use_info.network == 0
    assert decoded.origin.path() == "44'/60'/0'"
    assert decoded.children.path() == "0/*"
    assert account.address
    assert len(decoded.key) == 33
    assert len(decoded.chain_code) == 32


@pytest.mark.parametrize(
    "wallet_profile, expected_type, expected_prefix, min_pages",
    [
        ("metamask", "crypto-hdkey", "UR:CRYPTO-HDKEY/1-", 2),
        ("rabby", "crypto-hdkey", "UR:CRYPTO-HDKEY/1-", 2),
        ("tokenpocket", None, "0x", 1),
        ("bitget", "crypto-multi-accounts", "UR:CRYPTO-MULTI-ACCOUNTS/", 1),
        ("okx", "crypto-multi-accounts", "UR:CRYPTO-MULTI-ACCOUNTS/1-", 2),
    ],
)
def test_build_connect_qr_bundle_profiles(
    wallet_profile, expected_type, expected_prefix, min_pages
):
    from krux.web3 import build_connect_qr_bundle

    wallet = make_wallet()
    bundle = build_connect_qr_bundle(wallet.key, wallet_profile=wallet_profile)

    if expected_type is None:
        assert bundle.ur is None
        assert bundle.text == bundle.pages[0]
    else:
        assert bundle.ur is not None
        assert bundle.ur.type == expected_type
    assert len(bundle.pages) >= min_pages
    assert bundle.pages[0].startswith(expected_prefix)
    assert_display_ready_qr_bundle(bundle, expected_prefix[:3])


def test_fixed_mnemonic_web3_connect_profiles_are_display_ready():
    from krux.web3 import (
        WEB3_WALLET_PROFILE_BITGET,
        WEB3_WALLET_PROFILE_METAMASK,
        WEB3_WALLET_PROFILE_OKX,
        WEB3_WALLET_PROFILE_RABBY,
        WEB3_WALLET_PROFILE_TOKENPOCKET,
        build_connect_qr_bundle,
        derive_web3_account,
    )

    wallet = make_wallet()
    account = derive_web3_account(wallet.key)

    assert account.display_address == "0x9858EfFD232B4033E47d90003D41EC34EcaEda94"

    for wallet_profile in (
        WEB3_WALLET_PROFILE_OKX,
        WEB3_WALLET_PROFILE_BITGET,
        WEB3_WALLET_PROFILE_METAMASK,
        WEB3_WALLET_PROFILE_RABBY,
        WEB3_WALLET_PROFILE_TOKENPOCKET,
    ):
        bundle = build_connect_qr_bundle(wallet.key, wallet_profile=wallet_profile)

        expected_prefix = "0x" if wallet_profile == WEB3_WALLET_PROFILE_TOKENPOCKET else "UR:"
        assert_display_ready_qr_bundle(bundle, expected_prefix)


def test_sign_web3_request_uses_full_derivation_path():
    from krux.web3 import (
        Web3Request,
        Web3RequestDataType,
        derive_web3_address,
        normalize_eth_address,
        sign_web3_request,
    )

    wallet = make_wallet()
    path = "m/44h/60h/0h/0/1"
    address = derive_web3_address(wallet.key, path)

    assert address != derive_web3_address(wallet.key, "m/44h/60h/0h/0/0")

    request = Web3Request(
        source_format="ur",
        data_type=Web3RequestDataType.PERSONAL_MESSAGE,
        chain_id=1,
        derivation_path=path,
        address=normalize_eth_address(address),
        origin="pytest",
        request_id_value=b"req-full-path",
        request_id_text="req-full-path",
        sign_data=b"full path message",
        raw_payload="pytest",
        message_text="full path message",
    )

    result = sign_web3_request(wallet.key, request)

    assert result.signer_address == normalize_eth_address(address)


def test_parse_ur_eth_sign_request_and_build_signature_bundle():
    from ur.ur import UR
    from urtypes.cbor import Decoder as CborDecoder

    from krux.web3 import (
        Web3RequestDataType,
        parse_ur_eth_sign_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    request_ur = build_ur_eth_sign_request(wallet, b"Hello, Bob!")
    request = parse_ur_eth_sign_request(request_ur)
    result = sign_web3_request(wallet.key, request)
    decoded = CborDecoder(io.BytesIO(bytes(result.qr_bundle.ur.cbor))).decode()

    assert isinstance(request_ur, UR)
    assert request.source_format == "ur"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.chain_id == 1
    assert request.derivation_path == "m/44'/60'/0'/0/0"
    assert request.message_text == "Hello, Bob!"
    assert request.origin == "krux"
    assert result.request is request
    assert result.signer_address
    assert len(result.signature_bytes) == 65
    assert result.qr_bundle.ur.type == "eth-signature"
    assert_display_ready_qr_bundle(result.qr_bundle, "UR:ETH-SIGNATURE/")
    assert decoded[1] == "req-1"
    assert decoded[2] == result.signature_bytes
    assert decoded[3] == "krux"


def test_parse_tp_personal_sign_request_and_response():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_web3_request,
        _rlp_decode,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "hello web3",
            "dappName": "Krux",
            "source": "krux",
        },
    )
    request = parse_web3_request(raw)
    result = sign_web3_request(wallet.key, request)
    expected_data = json.dumps(
        {"signature": result.signature_hex, "address": result.signer_address},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    expected_response = (
        "tp:personalSignSignature-version=1.0&protocol=ArbitrumWallet"
        "&network=ethereum&chain_id=1&requestId=req-1&data="
        + expected_data
    )

    assert request.source_format == "tp"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.message_text == "hello web3"
    assert request.address == expected_address
    assert request.origin == "krux"
    assert result.signer_address == expected_address
    assert result.qr_bundle.text == expected_response
    assert result.qr_bundle.pages == [expected_response]
    assert_display_ready_qr_bundle(result.qr_bundle, "tp:personalSignSignature-")


def test_parse_tpr1_personal_sign_request_and_response():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_web3_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    inner = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "hello relay",
            "dappName": "Krux",
            "source": "krux",
        },
        request_id="req-relay",
    )

    request = parse_web3_request(build_tpr1_pages(inner, chunk_chars=500)[0])
    result = sign_web3_request(wallet.key, request)

    assert request.source_format == "tpr1"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.message_text == "hello relay"
    assert result.qr_bundle.text.startswith("tp:personalSignSignature-")
    assert "req-relay" in result.qr_bundle.text


def test_parse_w3r1_personal_sign_request_and_response():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_web3_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    inner = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "hello bridge",
            "dappName": "Bridge",
            "source": "bridge",
        },
        request_id="req-w3r1",
    )

    request = parse_web3_request(build_w3r1_pages(inner, chunk_chars=1200)[0])
    result = sign_web3_request(wallet.key, request)

    assert request.source_format == "w3r1"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.relay_wallet_name == "OKX Wallet"
    assert request.relay_format == "Keystone / AirGap UR"
    assert request.relay_qr_type == "eth-sign-request"
    assert result.qr_bundle.text.startswith("tp:personalSignSignature-")
    assert "req-w3r1" in result.qr_bundle.text


def test_parse_scanned_web3_request_accepts_raw_relay_json_envelope():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_scanned_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    inner = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "hello raw relay json",
            "dappName": "Bridge",
            "source": "bridge",
        },
        request_id="req-raw-json",
    )
    envelope = json.dumps(
        {
            "wallet_name": "OKX Wallet",
            "format": "Raw JSON",
            "payload": inner,
            "request_id": "relay-json-1",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    request = parse_scanned_web3_request(envelope)

    assert request.source_format == "w3r1"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.message_text == "hello raw relay json"
    assert request.relay_wallet_name == "OKX Wallet"


def test_parse_scanned_web3_request_accepts_urlencoded_tp_payload():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_scanned_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "hello urlencoded tp",
            "dappName": "TP",
            "source": "tp",
        },
        request_id="req-urlencoded",
    )

    request = parse_scanned_web3_request(urllib.parse.quote(raw, safe=""))

    assert request.source_format == "tp"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.message_text == "hello urlencoded tp"


def test_parse_scanned_web3_request_accepts_json_rpc_personal_sign():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_scanned_web3_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "jsonrpc-1",
            "method": "personal_sign",
            "params": ["hello json-rpc", expected_address],
            "origin": "Rabby",
            "chainId": "0x1",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    request = parse_scanned_web3_request(payload)
    result = sign_web3_request(wallet.key, request)

    assert request.source_format == "json-rpc"
    assert request.data_type == Web3RequestDataType.PERSONAL_MESSAGE
    assert request.message_text == "hello json-rpc"
    assert request.origin == "Rabby"
    assert result.qr_bundle.text.startswith("tp:personalSignSignature-")
    assert "jsonrpc-1" in result.qr_bundle.text


def test_parse_tp_typed_data_request_and_response():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_web3_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw = build_tp_raw_request(
        "signTypedData_v4",
        {
            "address": expected_address,
            "message": build_eip712_typed_data(),
            "dappName": "Krux",
            "source": "krux",
        },
        request_id="req-2",
    )
    request = parse_web3_request(raw)
    result = sign_web3_request(wallet.key, request)

    assert request.source_format == "tp"
    assert request.data_type == Web3RequestDataType.TYPED_DATA
    assert request.typed_data_json is not None
    assert request.address == expected_address
    assert result.signer_address == expected_address
    assert len(result.digest) == 32
    assert len(result.signature_hex) == 132
    assert result.qr_bundle.text.startswith("tp:signTypedData_v4Signature-")
    assert_display_ready_qr_bundle(result.qr_bundle, "tp:signTypedData_v4Signature-")
    assert "req-2" in result.qr_bundle.text


def _parse_tp_response_data(response_text):
    query = response_text.split("-", 1)[1]
    if query.startswith("?"):
        query = query[1:]
    params = urllib.parse.parse_qs(query, keep_blank_values=True)
    return json.loads(params["data"][0])


def _recover_signature_address(digest, signature_hex):
    from embit.util import secp256k1

    from krux.web3 import ethereum_address_from_pubkey, ethereum_checksum_address

    signature = bytes.fromhex(signature_hex[2:] if signature_hex.startswith("0x") else signature_hex)
    compact = signature[:64]
    rec_id = signature[64]
    if rec_id >= 27:
        rec_id -= 27
    recoverable = secp256k1.ecdsa_recoverable_signature_parse_compact(
        compact,
        rec_id,
    )
    pubkey = secp256k1.ecdsa_recover(recoverable, digest)
    pubkey_uncompressed = secp256k1.ec_pubkey_serialize(
        pubkey,
        secp256k1.EC_UNCOMPRESSED,
    )
    return ethereum_checksum_address(ethereum_address_from_pubkey(pubkey_uncompressed))


@pytest.mark.parametrize(
    "typed_data_builder, expected_chain_id",
    [
        (build_hyperliquid_spot_send_typed_data, int("0x66eee", 16)),
        (build_hyperliquid_l1_agent_typed_data, 1337),
    ],
)
def test_parse_tp_hyperliquid_typed_data_signs_and_recovers_address(
    typed_data_builder,
    expected_chain_id,
):
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_web3_request,
        sign_web3_request,
        typed_data_hash,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).display_address
    typed_data = typed_data_builder()
    typed_data_json = json.dumps(typed_data, ensure_ascii=False, separators=(",", ":"))
    raw = build_tp_raw_request(
        "signTypedData_v4",
        {
            "address": expected_address,
            "message": typed_data,
            "dappName": "Hyperliquid",
            "source": "https://app.hyperliquid.xyz",
        },
        request_id="hyperliquid-typed",
        chain_id=expected_chain_id,
    )

    request = parse_web3_request(raw)
    result = sign_web3_request(wallet.key, request)
    response_data = _parse_tp_response_data(result.qr_bundle.text)
    recovered_address = _recover_signature_address(result.digest, result.signature_hex)

    assert request.source_format == "tp"
    assert request.data_type == Web3RequestDataType.TYPED_DATA
    assert request.chain_id == expected_chain_id
    assert request.origin == "https://app.hyperliquid.xyz"
    assert request.typed_data_json == typed_data_json
    assert result.digest == typed_data_hash(typed_data_json)
    assert result.signer_address == derive_web3_account(wallet.key).address
    assert recovered_address == expected_address
    assert response_data["signature"] == result.signature_hex
    assert response_data["address"] == result.signer_address
    assert result.qr_bundle.text.startswith("tp:signTypedData_v4Signature-")
    assert_display_ready_qr_bundle(result.qr_bundle, "tp:signTypedData_v4Signature-")


def test_parse_tp_transaction_request_and_response():
    from krux.web3 import (
        EvmUnsignedTransaction,
        Web3RequestDataType,
        _encode_signed_transaction,
        _encode_unsigned_transaction,
        _rlp_decode,
        derive_web3_account,
        parse_web3_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw = build_tp_raw_request(
        "signTransaction",
        {
            "id": "req-tx",
            "address": expected_address,
            "txData": {
                "to": "0x1111111111111111111111111111111111111111",
                "value": "0",
                "data": "0x",
                "gasLimit": "21000",
                "nonce": "7",
                "gasPrice": "1",
                "type": 0,
            },
            "dappName": "Krux",
            "source": "krux",
        },
        request_id="req-tx",
    )
    request = parse_web3_request(raw)
    result = sign_web3_request(wallet.key, request)
    response_data = _parse_tp_response_data(result.qr_bundle.text)
    signed_bytes = bytes.fromhex(response_data["rawTransaction"][2:])

    assert request.source_format == "tp"
    assert request.data_type == Web3RequestDataType.TRANSACTION
    assert request.tp_request is not None and request.tp_request.kind == "transaction"
    assert result.signer_address == expected_address
    assert result.signature_bytes and len(result.signature_bytes) == 65
    assert result.signature_hex.startswith("0x")
    assert result.qr_bundle.text.startswith("tp:signTransactionSignature-")
    assert_display_ready_qr_bundle(result.qr_bundle, "tp:signTransactionSignature-")
    assert response_data["id"] == "req-tx"
    assert isinstance(_rlp_decode(signed_bytes), list)
    assert len(_rlp_decode(signed_bytes)) == 9

    unsigned = EvmUnsignedTransaction(
        tx_type=0,
        chain_id=1,
        nonce=7,
        gas_limit=21000,
        to=bytes.fromhex("1111111111111111111111111111111111111111"),
        value=0,
        data=b"",
        gas_price=1,
    )
    assert isinstance(_rlp_decode(_encode_unsigned_transaction(unsigned)), list)
    assert len(_rlp_decode(_encode_unsigned_transaction(unsigned))) == 9
    assert isinstance(_rlp_decode(_encode_signed_transaction(unsigned, 1, 1, 1)), list)
    assert len(_rlp_decode(_encode_signed_transaction(unsigned, 1, 1, 1))) == 9


def test_parse_tp_typed_transaction_request_and_response():
    from krux.web3 import (
        Web3RequestDataType,
        derive_web3_account,
        parse_web3_request,
        _rlp_decode,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw = build_tp_raw_request(
        "signTransaction",
        {
            "id": "req-typed-tx",
            "address": expected_address,
            "txData": {
                "to": "0x1111111111111111111111111111111111111111",
                "value": "0",
                "data": "0x",
                "gasLimit": "21000",
                "nonce": "1",
                "maxFeePerGas": "1000000000",
                "maxPriorityFeePerGas": "100000000",
                "accessList": [],
                "type": 2,
            },
            "dappName": "Krux",
            "source": "krux",
        },
        request_id="req-typed-tx",
    )
    request = parse_web3_request(raw)
    result = sign_web3_request(wallet.key, request)
    response_data = _parse_tp_response_data(result.qr_bundle.text)
    signed_bytes = bytes.fromhex(response_data["rawTransaction"][2:])

    assert request.source_format == "tp"
    assert request.data_type == Web3RequestDataType.TYPED_TRANSACTION
    assert request.tp_request is not None and request.tp_request.kind == "typed_transaction"
    assert result.signer_address == expected_address
    assert result.qr_bundle.text.startswith("tp:signTransactionSignature-")
    assert_display_ready_qr_bundle(result.qr_bundle, "tp:signTransactionSignature-")
    assert response_data["id"] == "req-typed-tx"
    assert signed_bytes[0] == 0x02
    assert isinstance(_rlp_decode(signed_bytes[1:]), list)
    assert len(_rlp_decode(signed_bytes[1:])) == 12


def test_parse_ur_transaction_request_and_response():
    from krux.web3 import (
        EvmUnsignedTransaction,
        Web3RequestDataType,
        _encode_unsigned_transaction,
        derive_web3_account,
        parse_ur_eth_sign_request,
        sign_web3_request,
    )

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    unsigned = EvmUnsignedTransaction(
        tx_type=0,
        chain_id=1,
        nonce=0,
        gas_limit=21000,
        to=bytes.fromhex("1111111111111111111111111111111111111111"),
        value=0,
        data=b"",
        gas_price=1,
    )
    request_ur = build_ur_eth_sign_request(
        wallet,
        _encode_unsigned_transaction(unsigned),
        request_id="req-ur-tx",
        data_type=Web3RequestDataType.TRANSACTION,
    )
    request = parse_ur_eth_sign_request(request_ur)
    result = sign_web3_request(wallet.key, request)
    response_data = _parse_tp_response_data(result.qr_bundle.text)

    assert request.source_format == "ur"
    assert request.data_type == Web3RequestDataType.TRANSACTION
    assert request.address == expected_address
    assert result.qr_bundle.text.startswith("tp:signTransactionSignature-")
    assert_display_ready_qr_bundle(result.qr_bundle, "tp:signTransactionSignature-")
    assert response_data["rawTransaction"].startswith("0x")
    assert response_data["id"] == "req-ur-tx"
    assert result.signature_hex.startswith("0x")


@pytest.mark.parametrize("index_base", [0, 1])
def test_tp_multi_fragment_assembler_accepts_zero_and_one_based(index_base):
    from krux.web3 import TpMultiFragmentAssembler, parse_tp_multi_fragment

    payload = "hello web3"
    total = 2
    first_index = index_base
    second_index = index_base + 1
    first = parse_tp_multi_fragment(
        build_tp_multi_fragment_raw(payload, first_index, total, "hello ")
    )
    second = parse_tp_multi_fragment(
        build_tp_multi_fragment_raw(payload, second_index, total, "web3")
    )

    assembler = TpMultiFragmentAssembler()
    state, detail = assembler.accept(second)
    assert state == "progress"
    assert detail == "已接收分片 1/2"

    state, detail = assembler.accept(first)
    assert state == "complete"
    assert detail == payload


def test_parse_relay_fragment_and_inflate_tpr1():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    pages = build_tpr1_pages(payload, chunk_chars=120)

    prefix, decoded = decode_relay_payload(pages[0])
    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_accepts_plain_base64_payload():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    prefix, decoded = decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_accepts_urlencoded_plain_payload():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    encoded = urllib.parse.quote(payload, safe="")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    prefix, decoded = decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_accepts_urlencoded_base64_payload():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    encoded = urllib.parse.quote(encoded, safe="")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    prefix, decoded = decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_accepts_base64_urlencoded_text_payload():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    urlencoded_payload = urllib.parse.quote(payload, safe="")
    encoded = base64.urlsafe_b64encode(urlencoded_payload.encode("utf-8")).decode(
        "ascii"
    )
    encoded = encoded.rstrip("=")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    prefix, decoded = decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_accepts_raw_deflate_payload():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    encoded = base64.urlsafe_b64encode(_raw_deflate(payload.encode("utf-8"))).decode(
        "ascii"
    )
    encoded = encoded.rstrip("=")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    prefix, decoded = decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_accepts_gzip_payload():
    from krux.web3 import decode_relay_payload

    payload = "tp:personalSign-version=1.0&data=test"
    encoded = base64.urlsafe_b64encode(gzip.compress(payload.encode("utf-8"))).decode(
        "ascii"
    )
    encoded = encoded.rstrip("=")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    prefix, decoded = decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_uses_deflate_module_when_zlib_missing(monkeypatch):
    from .shared_mocks import DeflateIO
    from krux import web3

    payload = "tp:personalSign-version=1.0&data=test"
    compressed = _raw_deflate(payload.encode("utf-8"), wbits=-10)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
    crc = zlib.crc32(encoded.encode("utf-8")) & 0xFFFFFFFF
    page = f"tpr1:1/1.{crc}.{encoded}"

    monkeypatch.setattr(web3, "zlib", None)
    monkeypatch.setitem(sys.modules, "deflate", types.SimpleNamespace(DeflateIO=DeflateIO))

    prefix, decoded = web3.decode_relay_payload(page)

    assert prefix == "tpr1:"
    assert decoded == payload


def test_parse_relay_fragment_and_inflate_w3r1():
    from krux.web3 import RelayFragmentAssembler, inflate_relay_text, parse_relay_fragment

    inner = "tp:personalSign-version=1.0&data=test"
    pages = build_w3r1_pages(inner, chunk_chars=12)
    first = parse_relay_fragment(pages[0])
    assembler = RelayFragmentAssembler(first.prefix)
    state, detail = assembler.accept(first)
    assert state == "progress"
    assert detail == f"已接收分片 1/{len(pages)}"

    decoded = None
    for page in pages[1:]:
        fragment = parse_relay_fragment(page)
        state, detail = assembler.accept(fragment)
        if state == "complete":
            decoded = inflate_relay_text(detail)
            break

    assert decoded is not None
    assert '"payload":"' in decoded
    assert inner in decoded
