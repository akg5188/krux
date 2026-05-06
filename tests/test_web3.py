import base64
import io
import json
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


def build_tp_raw_request(action, data, request_id="req-1", legacy=False):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    query = [
        ("version", "1.0"),
        ("protocol", "ArbitrumWallet"),
        ("network", "ethereum"),
        ("chain_id", "1"),
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
    "wallet_profile, expected_type, min_pages",
    [
        ("metamask", "crypto-hdkey", 1),
        ("rabby", "crypto-hdkey", 1),
        ("tokenpocket", "crypto-hdkey", 1),
        ("bitget", "crypto-multi-accounts", 1),
        ("okx", "crypto-multi-accounts", 2),
    ],
)
def test_build_connect_qr_bundle_profiles(wallet_profile, expected_type, min_pages):
    from krux.web3 import build_connect_qr_bundle

    wallet = make_wallet()
    bundle = build_connect_qr_bundle(wallet.key, wallet_profile=wallet_profile)

    assert bundle.ur is not None
    assert bundle.ur.type == expected_type
    assert len(bundle.pages) >= min_pages
    assert bundle.pages[0].startswith("UR:")


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
    assert "req-2" in result.qr_bundle.text


def _parse_tp_response_data(response_text):
    query = response_text.split("-", 1)[1]
    if query.startswith("?"):
        query = query[1:]
    params = urllib.parse.parse_qs(query, keep_blank_values=True)
    return json.loads(params["data"][0])


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
