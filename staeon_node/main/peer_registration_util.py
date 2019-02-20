import datetime
from bitcoin import ecdsa_verify, ecdsa_recover, ecdsa_sign, pubtoaddr, privtoaddr

class InvalidPeerRegistration(Exception):
    pass

class InvalidSignature(InvalidPeerRegistration):
    pass

def register_peer(pk, domain):
    timestamp = datetime.datetime.now().isoformat()
    address = privtoaddr(pk)
    to_sign = "%s%s%s" % (domain, address, timestamp)
    registration = {
        'domain': domain,
        'payout_address': address,
        'timestamp': timestamp,
        'signature': ecdsa_sign(to_sign, pk)
    }
    return registration

def validate_peer_registration(reg):
    to_sign = "{domain}{payout_address}{timestamp}".format(**reg)
    try:
        pubkey = ecdsa_recover(to_sign, reg['signature'])
    except:
        raise InvalidSignature("Can't recover pubkey from signature")

    valid_address = pubtoaddr(pubkey) == reg['payout_address']
    valid_sig = ecdsa_verify(to_sign, reg['signature'], pubkey)

    if not valid_sig or not valid_address:
        raise InvalidSignature("Invalid Signature")
    return True

if __name__ == '__main__':
    def assert_raises(call, exception, msg):
        try:
            call()
        except exception:
            return
        assert False, msg

    pk = 'KwuVvv359oft9TfzyYLAQBgpPyCFpcTSrV9ZgJF9jKdT8jd7XLH2'
    assert validate_peer_registration(register_peer(pk, 'example.com'))

    bad_reg = {
        'payout_address': '18pvhMkv1MZbZZEncKucAmVDLXZsD9Dhk6',
        'domain': 'example.com',
        'signature': 'IDZKaA/TUds7wYy69tW3BcqR87m2AIqgoQlxesDEMfhEclhn4Mcc+8fhZMg3fepGt++UJZvWlZSZLIrscSshmtw=',
        'timestamp': '2019-02-14T13:06:04.835896'
    }
    assert_raises(
        lambda: validate_peer_registration(bad_reg), InvalidSignature:
        "Invalid peer registration sig not being caught"
    )