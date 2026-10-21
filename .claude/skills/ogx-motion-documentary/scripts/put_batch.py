# PUT local JPEGs to Higgsfield presigned URLs from a saved media_upload result; record key -> media_id.
import json, os, re, subprocess, sys
res, order = sys.argv[1], sys.argv[2].split(",")
ups = json.load(open(res))["uploads"]
ids = json.load(open("media_ids.json")) if os.path.exists("media_ids.json") else {}
for key, u in zip(order, ups):
    fn = re.search(r"@(\S+?\.jpg)", u["instructions"]).group(1)
    assert fn == f"{key}.jpg", (fn, key)
    r = subprocess.run(["curl", "-sS", "-X", "PUT", "-H", "Content-Type: image/jpeg", "--data-binary", f"@jpg/{key}.jpg",
                        "-o", "/dev/null", "-w", "%{http_code}", u["upload_url"]], capture_output=True, text=True)
    print(key, r.stdout, r.stderr[:100])
    if r.stdout == "200":
        ids[key] = u["media_id"]
json.dump(ids, open("media_ids.json", "w"), indent=1)
print(len(ids))
