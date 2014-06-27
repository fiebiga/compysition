import StringIO, hashlib, base64
from lxml import etree
from re import sub
import OpenSSL.crypto as crypto
from OpenSSL.test.util import b as crypto_b

xml = open('digest_body_x509.txt').read()

shaval = hashlib.sha1(xml).digest()
done = base64.standard_b64encode(shaval)

print shava1
print done
