# Cloudflare DNS & Nameserver Automation

Automation module for provisioning and managing Cloudflare account custom nameserver sets and DNS records.

## Usage
```python
from infra.cloudflare import create_nameserver_set, upsert_dns_record

# Create nameserver set
ns_set = create_nameserver_set(
    account_id="023e105f4ecef8ad9ca31a8372d0c353",
    name="Production nameservers",
    nameservers=[{"name": "ns1.example.com"}],
)

# Upsert DNS record
rec = upsert_dns_record(
    zone_id="zone_12345",
    record_type="A",
    name="api.example.com",
    content="192.0.2.1",
    proxied=True,
)
```
