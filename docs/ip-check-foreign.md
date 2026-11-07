# Patch for BrezhnevSA/happ-geodata

This adds automatically updated `geosite:ip-check-foreign` with all entries in
v2fly `category-ip-geo-detect` (including nested `include:` lists), minus
Russian TLDs and an editable non-RU exclusion list.

## How to apply

From the repository root run `git apply --check ip-check-foreign.patch` then
`git apply ip-check-foreign.patch`. Commit and run your Build HAPP geodata
workflow. The new list is generated immediately before minimal geosite build.

The optional `publish/ip-check-foreign.txt` report will be available if your
publishing step includes files in `publish/`.

## How to route with the published geosite.dat

For HAPP / Xray using `geosite.dat` from this repository:

```json
{
  "type": "field",
  "domain": ["ext:geosite.dat:ip-check-foreign"],
  "outboundTag": "YOUR_VPN_OUTBOUND"
}
```

For XKeen with the router's local `geosite_runetfreedom.dat`, the new category
WILL NOT BE PRESENT. Download your updated geosite.dat to a separate filename
(e.g. `geosite_happ.dat`) and use:

```json
{
  "type": "field",
  "domain": ["ext:geosite_happ.dat:ip-check-foreign"],
  "outboundTag": "vless-latvia"
}
```

Keep your existing `category-ru` / RU `DIRECT` rules before the foreign rule
as an additional precaution. The `direct` category (if matching) may override
IP-checker rules depending on order.

## Limitations

No repository has literally every IP-checker on the Internet. This mirrors the
latest upstream v2fly category. Automatically filtering by TLD cannot establish
service ownership; review and add domains to `ip-check-ru-exclude.txt` as needed.
The script raises an error rather than silently admitting unfilterable
keyword/regexp rules if upstream adds them later.
