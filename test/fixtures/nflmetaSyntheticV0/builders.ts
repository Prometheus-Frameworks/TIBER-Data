// Entirely invented subjects, IDs, dates and values. Never a source-backed witness.
import { NFLMETA_BASE_STATS } from '../../../src/contracts/nflmetaSyntheticV0/playerGame.js';
export const V1 = 'a'.repeat(64);
export const V2 = 'b'.repeat(64);
export const receipt = { fixtureId: 'synthetic-nflmeta-v0', receivedAt: '2030-01-02T12:00:00Z' };
export function playerPage() {
  const counts = Object.fromEntries(NFLMETA_BASE_STATS.map(key => [key, null]));
  const statuses = Object.fromEntries(NFLMETA_BASE_STATS.map(key => [key, 'not_reported']));
  return {
    data: [{
      ...counts, pass_att: 10, pass_cmp: 6, pass_int: 0, rush_yds: -2, def_sacks: 0.5,
      stat_status: { ...statuses, pass_att: 'reported', pass_cmp: 'reported', pass_int: 'reported',
        rush_yds: 'reported', def_sacks: 'reported', targets: 'missing', rec: 'partial' },
      player_id: 900001, player_key: 'synthetic-player-a', display_name: 'Synthetic Player A',
      position: 'QB', position_group: 'offense', resolved_player: true, game_id: 800001,
      season_year: 2030, season_type: 'REG', week: 1, round: null, game_date: '2030-01-01',
      team_abbr: 'SYN-A', opponent_abbr: 'SYN-B', home_away: 'home', result: 'W',
      rank: 1, stat_value: 0, stat_version: V1, boxscore_updated_at: '2030-01-02T11:00:00Z',
    }],
    meta: {
      contract_version: '2', missing_stat_policy: 'null_with_stat_status',
      stat_version_semantics: 'player_game_content_sha256_not_a_sequence',
      boxscore_updated_at_semantics: 'latest_contributing_boxscore_row_write_not_correction_time',
      correction_history_available: false, total: 1, returned: 1, limit: 100, offset: 0,
      has_more: false, season_year: 2030, season_type: 'REG', stat: 'pass_int', order: 'desc',
      filters: { min_targets: null }, coverage_note: 'Synthetic filtered query only',
    },
  };
}
export function mapping(id = 1) {
  return {
    mapping_id: id, player_key: `synthetic-player-${id}`, canonical_player_key: `synthetic-player-${id}`,
    sleeper_player_id: String(900000 + id), verified_at: '2030-01-02T10:00:00Z',
    status: 'verified', alias_keys: [`synthetic-alias-${id}`],
  };
}
export function mappingPage(offset = 0, total = 2, limit = 1) {
  const returned = Math.min(limit, total - offset);
  const hasMore = offset + returned < total;
  return {
    data: Array.from({ length: returned }, (_, i) => mapping(offset + i + 1)),
    meta: {
      total, limit, offset, snapshot_id: total, after_id: 0, returned, max_page_size: 100,
      next_offset: hasMore ? offset + returned : null, max_result_window: 1000,
      version_bound: offset !== 0, page_complete: true, not_modified: false, has_more: hasMore,
      complete: !hasMore, can_complete: true, window_blocked: false, version: V1,
      sync_type: 'full', scope: 'published_registry', consistency: 'version_bound_restart_on_change',
      next_page: hasMore ? `/api/v1/players/cross-references?provider=sleeper&limit=${limit}&offset=${offset + returned}&snapshot_id=${total}&version=${V1}` : null,
      last_checked_at: '2030-01-02T10:00:00Z', refresh_schedule: 'hourly_check_with_24_hour_minimum',
      unmapped_meaning: 'Unknown, never inactive',
    },
  };
}
