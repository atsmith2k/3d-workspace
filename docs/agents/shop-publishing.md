# Shop publishing: from a design here to a live product on shop.ash10.dev

The shop is a separate repo, `ash10-dev-shop` (Next.js, deployed on the user's own "ash10"
VM panel, not Vercel). It ingests manifests that this workspace writes into `output/`. This
is the path the grizzly, Harvest Hollow and Frost & Fir took on 2026-11-02.

## 1. Build the product here

- 3D model: `cad publish models/<name>.py --refresh` writes `output/<name>/manifest.json`
  (`cadkit-product/1`), product and hero renders, 3MFs, print notes.
- Embroidery: `cad stitch publish designs/<name>.py` builds every size in `SIZES` in eight
  formats plus the SVG, checks each with stitchsim (`problems 0` required), renders the
  product shot, garment mockups and thread chart, writes buyer notes, `<slug>.zip` (one
  folder per size) and `manifest.json` (`cadkit-embroidery/1`, `kind: "embroidery"`, with
  suggested `shop` prices for the user to confirm).
  `cad stitch bundle <collection> --title ... --blurb ...` makes the collection bundle.
  A design built at one size only can get a manifest from the shop's
  `scripts/publish/embroidery-manifest.py`.
- Set `PRODUCT["draft"] = True` (the collection helpers do): the manifest carries
  `shop.draft: true` and the design goes to the review queue instead of on sale.

## 2. Publish into the shop

From an `ash10-dev-shop` checkout **on an up-to-date `main`** (the user's main checkout is
often parked on an old feature branch; check `git branch --show-current` and pull):

```bash
node --env-file=.env.publish scripts/publish/publish-models.mts --workspace ../3d-workspace/output
```

That is a dry run; add `--apply` to write. It ingests both manifest kinds (models and
embroidery), creates a personal and a commercial product per design, and uploads the files.

- **Drafts**: designs with `shop.draft` land in the admin's Draft Products queue
  (`/admin/drafts`), where the user swipes approve or send back with a critique. Read the
  critiques with
  `node --env-file=.env.publish scripts/publish/review-queue.mts --state changes_requested --json`,
  redesign, and re-publish the same slug (the revision bumps). A routine re-publish never puts
  an unreviewed draft on sale.
- **Held**: `scripts/publish/held.json` names slugs that every publish run lists as
  "Coming soon" (visible, never purchasable, checkout refuses them) whatever the manifest
  says. Use it for anything waiting on the user (a licence answer, a price).
- **Prices and going live are the user's decision.** Suggested prices are suggestions; ask,
  then record what they approved in the commit message.

## 3. Production gotchas

- **Every deploy of the shop empties its files** (stopgap storage inside the release folder
  on the VM). After any deploy of `main`, re-run the publish with `--apply`; it is idempotent
  and keeps the same URLs. Don't add new storage without the user (it needs SSH to the VM).
- The shop's file upload takes **200 MB at most** (`413 payload_too_large`; a 502 with an empty
  body can be the same thing at the proxy). Bundle zips leave out each member's product shot
  for this reason (Game Day States, 104 designs, came to 229 MB with them). Rebuild bundles
  (`cad stitch bundle`) after re-publishing their designs, or they ship the old member zips.
- Never press the panel's "Create database": it replaces `DATABASE_URL` with an empty one
  at once.
- The Etsy shop carries molds and clay cutters only; don't claim embroidery there.
- Shop copy speaks of "designs" and "design files" (the shop sells more than 3D models now);
  a product's own page names its formats.

## 4. Verify in production

A design is delivered when, on https://shop.ash10.dev after the latest deploy and re-publish:
its page loads with images and facts (size, hoop, stitches, threads, sew time for
embroidery), every download in the pack works, its collection and the landing page list it,
and checkout behaves as intended (buys when on sale, refuses when held or draft). Report the
live URLs and what you checked.

## Rights and licences

- Commercial licence: any quantity, matching the shop's licence page.
- A design derived from someone else's image, published model or datasheet stays held until
  the user confirms the rights. No franchise, character, school, team or brand names, marks
  or styles in designs, titles or tags.
