# Publishing this project to GitHub

## Option A — automated push (token)

1. Create a **fine-grained personal access token**:
   GitHub → Settings → Developer settings → Personal access tokens →
   **Fine-grained tokens** → *Generate new token*
   * Repository access: **All repositories** (or select the target repo)
   * Permissions: **Contents → Read and write**, *Metadata → Read*
   * Expiration: shortest that works for you
2. From the project folder:

```bash
cd superteamtr-tshirt-design

# create the repo on your account (change the name if you like)
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"name":"superteamtr-tshirt-design","description":"SuperteamTR T-shirt — ARENA PROTOCOL (Colosseum / crypto expo concept), production-ready vector artwork","private":false,"has_issues":true}'

git remote add origin https://github.com/<YOUR-USERNAME>/superteamtr-tshirt-design.git
git branch -M main
git push -u origin main
```

3. Revoke the token when you are done (Settings → Developer settings → Tokens).

## Option B — manual push

```bash
cd superteamtr-tshirt-design
git remote add origin https://github.com/<YOUR-USERNAME>/superteamtr-tshirt-design.git
git branch -M main
git push -u origin main
```

The repository already contains a single commit with all 138 files and a
`.gitignore`. Nothing else is required.

## Repo description / topics (suggested)

> Production-ready T-shirt design for SuperteamTR — Colosseum rebuilt as a
> futuristic Web3 arena, Solana at its centre. Vector masters, print
> separations, mockups and documentation.

Topics: `solana` `superteam` `tshirt-design` `merch` `vector-art` `screen-print` `web3`
