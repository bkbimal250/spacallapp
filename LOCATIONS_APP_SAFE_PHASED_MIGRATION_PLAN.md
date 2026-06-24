# Locations App Safe Phased Migration Plan

This plan creates the normalized locations system while keeping all existing
spa/branch location text fields intact until the full migration is verified.

Existing text fields may include `state`, `city`, `area`, `address`, or similar
fields on spa/branch models. These fields must not be deleted, renamed,
overwritten, or made secondary in storage during the initial implementation.
They remain available as legacy/reference data until a later confirmed removal
task.

## Current Repository Status

As of this plan update, the repository already contains a partial
`apps.locations` implementation:

- `apps.locations` is installed in Django settings.
- `/api/v1/locations/` is included in the main URL configuration.
- Location models currently include `State`, `City`, `CityAlias`, `Area`,
  `AreaAlias`, `LocationGroup`, `LocationGroupArea`, `BranchCoverageArea`, and
  `LocationMatchIgnorePhrase`.
- Location serializers, filters, and API views are present.
- `apps.branches.models.Branch` still stores legacy text fields named `state`,
  `city`, `area`, `postal_code`, and `address`.
- `apps.locations.admin` is still empty.
- `apps.locations.tests` is still empty.
- `apps.locations.migrations` currently has no generated model migration.
- Backfill and audit management commands are not present yet.

Because `Branch.state`, `Branch.city`, and `Branch.area` already exist as text
fields, the Phase 2 FK fields must use non-conflicting transitional names unless
and until a later, separate rename/removal task is approved.

## Migration Rules

- Never delete old spa/branch location text fields in the current task.
- Never overwrite old text location fields during backfill or new writes.
- Add new normalized fields in a backward-compatible way.
- Do not reuse existing legacy field names for new FKs when those names already
  exist as text fields.
- New bot/location logic should prefer normalized FK fields.
- Old text fields are fallback/reference only during the transition.
- Migrations are created only; they are not applied by automation.
- Final removal of old text fields must be a separate migration, PR, and task.

## Phase 0: Safety Baseline Before Any Code Change

Before implementing or generating migrations, confirm the current branch/spa
model fields and all active readers/writers:

- Inventory legacy fields on `apps.branches.models.Branch`: `state`, `city`,
  `area`, `postal_code`, and `address`.
- Search backend serializers, filters, views, reports, bots, DoubleTick, Android
  APIs, and frontend branch forms for legacy location field usage.
- Mark each usage as one of:
  - `display_reference`: safe to keep during migration.
  - `fallback_match`: allowed only when normalized FK is empty.
  - `primary_logic`: must be migrated before deprecation mode.
  - `write_path`: must not overwrite legacy text during this migration.
- Do not apply migrations from automation. The operator will run migrations
  manually after review.
- Keep old data readable at every phase.
- Keep old APIs backward compatible while adding normalized FK data.

Recommended first checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Phase 1: Create New Locations App

Create or complete the `locations` app with normalized models and supporting
behavior:

- `State`
- `City`
- `CityAlias`
- `Area`
- `AreaAlias`
- `LocationGroup`
- `LocationGroupArea`
- `BranchCoverageArea`
- Matching service
- APIs
- Admin
- Tests
- Management commands

The matching service should normalize user-entered or imported location text and
return confident matches for state, city, area, group, and branch coverage while
flagging ambiguous or unmatched data for manual review.

Implementation status:

- Models are partially present.
- APIs are partially present.
- Admin registration still needs to be completed.
- Tests still need to be written.
- Initial migrations still need to be generated.
- Matching behavior should be moved into a reusable service instead of living
  only in API view code.
- Backfill/audit management command folders still need to be added.

Phase 1 implementation tasks:

- Move matching logic from `LocationMatchAPIView.match_text()` into
  `apps.locations.services.LocationMatchingService`.
- Keep the API view as a thin wrapper around the service.
- Add admin registration for every model with useful list display, search, and
  filters.
- Add tests for normalization, alias matching, ignore phrases, group/area city
  validation, and branch coverage validation.
- Add `apps.locations.management.commands` package.
- Generate a locations initial migration only after models/admin/services/tests
  are reviewed.

## Phase 2: Add Nullable FK Fields To Existing Spa/Branch Model

Add nullable FK fields to the existing spa/branch model:

- state FK
- city FK
- location_group FK
- area FK

Do not remove old text fields.
Do not rename old text fields.
Do not make the new FK fields required yet.

In this repository, `Branch.state`, `Branch.city`, and `Branch.area` already
exist as legacy text fields. Therefore the new nullable FK fields should use
explicit transitional names:

- `location_state` -> `locations.State`
- `location_city` -> `locations.City`
- `location_group` -> `locations.LocationGroup`
- `location_area` -> `locations.Area`

Document these as the normalized location fields in model comments, serializers,
and admin. Do not rename legacy fields in this phase.

Phase 2 implementation tasks:

- Add nullable FK fields to `Branch`:
  - `location_state = ForeignKey("locations.State", null=True, blank=True, on_delete=SET_NULL, related_name="branches")`
  - `location_city = ForeignKey("locations.City", null=True, blank=True, on_delete=SET_NULL, related_name="branches")`
  - `location_group = ForeignKey("locations.LocationGroup", null=True, blank=True, on_delete=SET_NULL, related_name="branches")`
  - `location_area = ForeignKey("locations.Area", null=True, blank=True, on_delete=SET_NULL, related_name="branches")`
- Add indexes for `location_state`, `location_city`, `location_group`, and
  `location_area`.
- Expose read/write FK IDs and read-only names in branch serializers.
- Keep existing text fields in serializers for compatibility.
- Do not change existing required validation for old fields in this phase.
- Do not migrate old values automatically in the schema migration.

## Phase 3: Backfill And Manual Mapping

Create a management command:

```bash
python manage.py backfill_locations_from_spas --dry-run
python manage.py backfill_locations_from_spas --commit
```

The command must:

- Read old spa/branch state, city, and area text fields.
- Create or match new `State`, `City`, and `Area` records.
- Set `location_state`, `location_city`, `location_group`, and `location_area`
  only when the match is confident.
- Print ambiguous rows.
- Print unmatched rows.
- Never delete old data.
- Never overwrite old text fields.
- Support dry-run mode by default or through `--dry-run`.
- Require `--commit` before writing FK mappings.

Ambiguous mappings should be left unchanged and reported with enough identifying
information for manual correction in the CRM.

Backfill confidence rules:

- Exact normalized state + exact normalized city + exact normalized area can be
  committed automatically.
- Exact city alias and exact area alias can be committed automatically when the
  state or city context leaves only one candidate.
- Area-only matches across multiple cities are ambiguous and must be reported.
- City-only matches can set `location_state` and `location_city`, but must leave
  `location_area` empty.
- Group should be set only when the matched area belongs to exactly one active
  `LocationGroupArea`, or when a branch group/manual mapping confirms it.
- Existing normalized FK values should not be overwritten unless an explicit
  `--replace-existing` option is added later and manually approved.

Command output should include:

- Created states, cities, areas, aliases, and groups.
- Updated branch FK counts.
- Skipped branches with existing FK values.
- Ambiguous branch rows with branch id, code, spa name, old state/city/area, and
  candidate matches.
- Unmatched branch rows with branch id, code, spa name, old state/city/area.
- A final reminder that old text fields were not changed.

## Phase 4: CRM UI Update

Update the spa/branch edit UI:

- Show new cascading selects: State -> City -> Group -> Area.
- Keep old text fields visible as legacy/reference when needed.
- Allow admins to manually correct mappings.
- Save `location_state`, `location_city`, `location_group`, and
  `location_area`.
- Treat old text fields as non-primary after a normalized mapping exists.

The UI should make the normalized location fields the operational source for new
workflows while keeping legacy values available for comparison and cleanup.

CRM UI implementation tasks:

- Add locations API client methods for states, cities, groups, and areas.
- In branch create/edit forms, load dependent options in this order:
  State -> City -> Group -> Area.
- Display legacy `state`, `city`, `area`, and `address` as reference fields or
  clearly separated legacy fields.
- Save normalized FK IDs to the branch API.
- In branch list/detail views, prefer normalized names when present and show
  legacy names only as fallback/reference.
- Add admin correction workflow for unmatched or ambiguous branches from the
  backfill report.

## Phase 5: Bot And DoubleTick Integration Shift

Update bots and DoubleTick matching to use the normalized location models:

- City maps to `locations.City`.
- Area maps to `locations.Area`.
- Group maps to `locations.LocationGroup`.
- Branch maps to the existing spa/branch model through `location_state`,
  `location_city`, `location_group`, and `location_area`.
- Old text fields are used only as fallback/reference for manual review.
- New bot decisions should not rely on old text fields when normalized FKs are
  available.

DoubleTick lead classification should resolve city, area, group, and branch
against the normalized location system. It should stop treating raw free-text
location fields as the primary classification source once normalized matches
exist.

Phase 5 implementation tasks:

- Replace direct `Branch.city` and `Branch.area` decision logic with
  `Branch.location_city` and `Branch.location_area` when present.
- Update dynamic bot city/area/group options to read from `locations` models.
- Keep legacy text fields only as fallback labels when normalized data is empty.
- Update DoubleTick area matching to call `LocationMatchingService`.
- Store raw customer text in raw fields for audit, but store normalized matches
  through FK fields or linked mapping records.
- Do not write customer city text into `raw_area` when the text is classified as
  a city.
- Use `BranchCoverageArea` to decide which branches can receive leads for a
  matched area.

## Phase 6: Verification Before Deletion

Create an audit command:

```bash
python manage.py audit_location_migration
```

The audit must check:

- Branches without state FK.
- Branches without city FK.
- Branches without area FK.
- Branches with invalid FK combinations, such as area and group from different
  cities.
- Branches still using old location text in APIs.
- Bot code still reading old location fields as primary inputs.
- Frontend still displaying old fields as primary.
- DoubleTick matching still writing city into `raw_area`.
- Leads without proper city, area, or group mapping.
- Leads without proper branch mapping.
- Duplicate city records.
- Duplicate area records.
- Ambiguous mappings.
- Missing `BranchCoverageArea` rows for active branches that should receive
  area leads.

Do not delete old fields unless this audit passes and the result has been
manually reviewed.

Audit command output should be grouped into:

- `Schema`: confirms normalized FK fields exist and legacy fields still exist.
- `Branch mapping`: missing state/city/group/area FKs and invalid combinations.
- `Location data`: duplicates, inactive references, ambiguous aliases.
- `Coverage`: active branches without `BranchCoverageArea` coverage.
- `Backend usage`: code paths still using legacy fields as primary.
- `Frontend usage`: screens still showing legacy fields as primary.
- `Bot/DoubleTick`: decisions still using old text fields first.
- `Lead health`: leads/conversations without normalized city/area/group/branch.
- `Deletion readiness`: PASS only when every blocker is zero.

The audit must exit with a non-zero status when deletion readiness fails, so old
field removal cannot be treated as safe accidentally.

## Phase 7: Deprecation Mode

After all screens, APIs, bots, and DoubleTick flows use the new FK fields:

- Mark old fields as deprecated in code comments.
- Make old fields read-only in admin/frontend if still visible.
- Stop writing new data into old fields.
- Keep old fields only for historical reference temporarily.

Legacy field writes should be blocked or ignored for new workflows, but existing
stored values must remain available for audit and rollback safety.

Deprecation mode rules:

- Add code comments on legacy Branch fields explaining they are historical.
- Make old fields read-only in admin/frontend where practical.
- Stop new backend write paths from changing old fields.
- Keep serializers backward compatible for old clients.
- Continue showing old values in detail/audit screens for comparison.
- Run `audit_location_migration` after every related release.

## Phase 8: Final Removal Migration

Only after explicit confirmation:

- Create a separate migration to remove old state/city/area text fields.
- Do not include this deletion in the first implementation.
- Keep final removal as a separate PR/task.
- Run the audit command again before and after the removal migration.

The final removal task should include its own review checklist, rollback plan,
and confirmation that no active code path reads or writes the legacy fields.

Final removal hard gate:

- Do not create the removal migration in the current task.
- Do not remove `Branch.state`, `Branch.city`, `Branch.area`, `Branch.address`,
  or similar legacy fields until the user explicitly approves a separate final
  removal task.
- Keep old data export available before the removal migration.
- Keep rollback notes in the final PR.

## Implementation Order For Next Developer Task

Use this order when implementation starts:

1. Complete `apps.locations` admin, services, tests, and management command
   package.
2. Add nullable normalized FK fields to `Branch` without touching old fields.
3. Add migrations, but do not apply them.
4. Add `backfill_locations_from_spas` with dry-run default and `--commit`.
5. Add `audit_location_migration`.
6. Update branch serializers and APIs to include normalized FK data.
7. Update CRM branch UI cascading selects.
8. Update bot and DoubleTick matching to prefer normalized locations.
9. Run tests and audit.
10. Stop. Do not delete old fields.

## Expected Final Behavior

- The new locations app works.
- Spa branches are mapped using State -> City -> Group -> Area.
- Bot flows use normalized location data.
- DoubleTick leads classify city, area, group, and branch correctly.
- CRM and Android show correct city, area, and branch information.
- Old fields remain until everything is verified.
- Old fields are deleted only later through a separate final migration.
