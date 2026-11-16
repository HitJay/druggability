# Novo Nordisk Research Data Services (`sc177` OData v4 & `novopy` Backend) Integration

> Updated: 2026-11-09  
> Module: `src/druggability/nn_data_service.py` (`NNDataServiceClient`)  
> CLI: `scripts/nn_data_service_cli.py`  
> Tests: `tests/test_nn_data_service.py`

---

## 1. Overview

`https://sc177.corp.novocorp.net` is the internal Novo Nordisk IIS/ASP.NET OData v4 gateway backing the `novopy` Python SDK (`https://midgard-prd.portal-prd.heimdall.novonordisk.cloud/docs/default/Component/novopy/notebooks/services/eln/`).

Rather than exposing only ELN entries, `sc177` hosts **25+ research data microservices**, each providing:
- Swagger 2.0 specification (unauthenticated): `https://sc177.corp.novocorp.net/<Service>/v1/swagger/docs/v1`
- OData v4 EDM metadata (unauthenticated): `https://sc177.corp.novocorp.net/<Service>/v1/odata/$metadata`
- OData v4 entity endpoints (authenticated via Kerberos SPNEGO `Negotiate` or OAuth2 `Bearer`).

### Key Microservices Mapped to Core Workflows

| Microservice | Base Path | Key Entities / Operations | Primary Value for Imaging / Safety / Druggability |
|---|---|---|---|
| **BioviaRendering** | `/BioviaRendering/v1` | `POST /render/from-string`, `GET /healthz` | **Unauthenticated** 2D depiction from V2000/V3000 Molblock into PNG (`format=1`), JPEG (`format=2`), or EMF vector (`format=3`). |
| **NNExperiments** | `/NNExperiments/v1/odata` | `Experiments`, `Entries`, `Entries({Id})/Render`, `AttachedFiles` | Pull wet-lab ELN protocols, ECHO 525 plate maps (e.g. `IGWU` myotube screening, `UHYG` HepG2-TMRM), and latest target knockdown notes (e.g. `GRB14` / `GRB10` KD). |
| **NNSamples** | `/NNSamples/v1/odata` | `LibraryOverviews`, `Pools`, `Samples` | Map plate barcodes (`ContainerLabel`) and wells (`WellTag`) to siRNA/compound `Pools` (`GeneSymbol`, `GeneId`, `Sequence`, `Extreg`). |
| **NNStructures** | `/NNStructures/v1/odata` | `PDBFiles`, `Structures`, `AttachedFiles` | Search and download proprietary internal X-ray / NMR co-crystal PDB files (`PdbFile`, `XrayResolution`, `XrayRFree`, `NncNo`). |
| **NNCompounds** | `/NNCompounds/v1/odata` | `Molecules`, `Molfiles`, `NNASProts`, `Nucleotides`, `CalculatedProperties` | Query registered small molecules, modified peptides (`NNASProt` / `ProteinModification`), and oligo/siRNA sense/antisense strands; supports `SubstructCTABSearch` and `SubSequenceSearch`. |
| **NNResults & NNProtocols** | `/NNResults/v1/odata`, `/NNProtocols/v1/odata` | `Results`, `ExperimentVarResults`, `Protocols` | Fetch internal wet-lab assay readouts (`ValueNumeric`, `RelationSign`, `Unit`) by `NNCNo` or `IdProtocol` for SAR and dry-wet calibration. |
| **NNBatches & NNAnnotations** | `/NNBatches/v1/odata`, `/NNAnnotations/v1/odata` | `MoleculeBatches`, `FormulationBatches`, `Topics` | Batch lineage, purity/salt forms, and project/topic annotations. |

---

## 2. Authentication on Linux HPC (`hpccnrd001`)

### Why Kerberos SPNEGO (`kinit`) is the Primary Channel
Azure AD Conditional Access enforces an Intune device compliance check on OAuth2 Device Code flows (`client_id=643ba961-8f41-4de3-acb5-be804de1d2d7`), blocking browser device-code logins initiated from unmanaged Linux HPC nodes (`hpccnrd001`).

Because `hpccnrd001` is domain-joined to `CORP.NOVOCORP.NET` and `sc177` natively accepts `WWW-Authenticate: Negotiate`, **Kerberos SPNEGO (`kinit`)** authenticates directly over the internal corporate network without any browser prompts or device-compliance blocks.

### One-Time Ticket Initialization (Valid 10h, Renewable 7d)
Run in an interactive HPC SSH terminal:

```bash
kinit -c /tmp/krb5cc_$(id -u) qyji@CORP.NOVOCORP.NET
```

To renew without re-entering the password within 7 days:
```bash
kinit -R -c /tmp/krb5cc_$(id -u)
```

`NNDataServiceClient` automatically detects `/tmp/krb5cc_<uid>`, verifies ticket validity via `klist -s`, and executes OData queries via `curl --http1.1 --negotiate -u : --cacert /etc/pki/tls/certs/ca-bundle.crt`.

---

## 3. CLI Usage (`scripts/nn_data_service_cli.py`)

```bash
# 1. Connectivity, Biovia PNG rendering & Kerberos auth check
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py probe

# 2. Search ELN experiments by owner initials (e.g. IGWU, NYOL, UHYG) or keyword (e.g. GRB14, myotube, HepG2)
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py eln --owner IGWU --top 10
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py eln --keyword GRB14 --top 10

# 3. List all entries & attachments in an ELN experiment, or render a specific entry (including plate tables) to plain text
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py eln-entry --exp-id 838941
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py eln-entry --exp-id 838941 --entry-id 10133509

# 4. Search proprietary internal co-crystal PDB structures
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py structures --query FcRn

# 5. Search internal siRNA pools by gene symbol or fetch well-level plate layout by barcode
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py sirna --gene XPO1
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py plate --barcode <ContainerLabel>

# 6. Fetch wet-lab assay readouts by NNC compound number
/data/user/QYJI/miniforge3/bin/python scripts/nn_data_service_cli.py results --nnc 0113
```

---

## 4. Python SDK Usage (`druggability.nn_data_service`)

```python
from druggability.nn_data_service import NNDataServiceClient

client = NNDataServiceClient()

# 1. Search ELN experiments and render entry HTML to text
exps = client.search_eln_experiments(keyword="GRB14", top=5)
entries = client.get_eln_entries(experiment_id=838941)
text = client.render_eln_entry_text(experiment_id=838941, entry_id=10133509)

# 2. Query internal X-ray / NMR PDB structures and download coordinates
structs = client.search_internal_structures("FcRn", top=5)
pdb_str = client.download_internal_pdb(pdb_id=1821)

# 3. Render 2D structure via BioviaRendering (PNG=1, JPEG=2, EMF=3)
png_bytes = client.render_molblock(molblock_str, image_format=1, width=400, height=400)
```

---

## 5. Engineering Notes & Pitfalls

1. **HTTP/1.1 Required for IIS Kerberos SPNEGO**:
   `sc177` runs Microsoft-IIS/10.0. Multi-leg GSSAPI/SPNEGO authentication is connection-oriented and fails over HTTP/2 (`curl: (28) HTTP/2 stream 0 was not closed cleanly: HTTP_1_1_REQUIRED (err 13)`). Always pass `--http1.1` when using `curl --negotiate`.
2. **Corporate CA Bundle**:
   Always pass `/etc/pki/tls/certs/ca-bundle.crt` (`SSL_CERT_FILE` or `--cacert`) so Novo Nordisk internal root/intermediate CAs validate cleanly across conda/venv environments.
3. **ELN Search Table Selection (`/odata/Experiments` vs `/odata/ExperimentsExtendeds`)**:
   Query `/odata/Experiments?$filter=IsRedacted eq false and ...` (~2.5s response) rather than `/odata/ExperimentsExtendeds` (>60s timeout due to unindexed role/keyword joins across ~900k rows).
4. **Access-Controlled (`IsRedacted`) Records**:
   Experiments or nucleotide sequences outside the user's AD project role return `IsRedacted: true` with `"********"` masked fields; filter with `IsRedacted eq false` when searching.
