"""Dars faylidan o'zbekcha ovoz matnlarini ($D/texts.json) tayyorlaydi.
Ishlatish: python tools/0_matnlar.py lessons/dars-NN.json ish/dars-NN
"Endi sizning navbatingiz!" har darsda bir xil, shuning uchun u qayta chiqarilmaydi: voice_uz/ref/turn.wav dan olinadi."""
import json, os, sys
les, out = json.load(open(sys.argv[1])), sys.argv[2]
for d in ("kokoro", "pre", "vc"):
    os.makedirs(f"{out}/{d}", exist_ok=True)
dot = lambda s: s if s[-1] in ".!?" else s + "."
t = {"hook": les["hook_say"]}
for i, it in enumerate(les["items"]):
    t[f"uz{i}"] = dot(it.get("uz_say") or it["uz"].split(" (")[0])      # uz_say: ekrandagidan boshqacha aytilsa
t["exuz"] = dot(les["example"]["uz"])
t["next"] = les["end_say"]
json.dump(t, open(f"{out}/texts.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(t, ensure_ascii=False, indent=1))
