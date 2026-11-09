import { z } from 'zod';
import { nflmetaDate, nflmetaHash, nflmetaInteger, nflmetaSyntheticEvidence,
  nflmetaText, nflmetaTimestamp } from './common.js';

export const NFLMETA_BASE_STATS = [
  'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_sacks',
  'pass_sack_yds_lost', 'rush_att', 'rush_yds', 'rush_td', 'targets', 'rec',
  'rec_yds', 'rec_td', 'fumbles', 'fumbles_lost', 'def_int', 'def_int_yds',
  'def_sacks', 'def_tkl_combined', 'def_tkl_solo', 'def_tkl_ast', 'def_ff', 'def_fr',
  'kick_returns', 'kick_return_yds', 'punt_returns', 'punt_return_yds',
  'fgm', 'fga', 'xpm', 'xpa', 'punts', 'punt_yds',
] as const;
export type NflmetaBaseStat = typeof NFLMETA_BASE_STATS[number];
const ratios = {
  pass_cmp_pct: ['pass_cmp', 'pass_att'], rush_yds_per_att: ['rush_yds', 'rush_att'],
  rec_yds_per_rec: ['rec_yds', 'rec'], catch_pct: ['rec', 'targets'],
  xp_pct: ['xpm', 'xpa'], punt_yds_per_punt: ['punt_yds', 'punts'],
  pass_td_pct: ['pass_td', 'pass_att'], fg_pct: ['fgm', 'fga'],
  pass_yds_per_att: ['pass_yds', 'pass_att'],
} as const;
const derivedStats = Object.keys(ratios) as (keyof typeof ratios)[];
const status = z.enum(['reported', 'missing', 'not_reported', 'partial']);
const statsShape = Object.fromEntries(NFLMETA_BASE_STATS.map(key => [key,
  (key === 'def_sacks' ? z.number().finite() : z.number().int().safe()).nullable(),
])) as Record<NflmetaBaseStat, z.ZodNullable<z.ZodNumber>>;
const statusShape = Object.fromEntries(NFLMETA_BASE_STATS.map(key => [key, status])) as
  Record<NflmetaBaseStat, typeof status>;
const derivedShape = Object.fromEntries(derivedStats.map(key => [key, z.number().finite().optional()])) as
  Record<keyof typeof ratios, z.ZodOptional<z.ZodNumber>>;

const rowSchema = z.object({
  ...statsShape, ...derivedShape,
  stat_status: z.object(statusShape).strict(), stat_version: nflmetaHash,
  boxscore_updated_at: nflmetaTimestamp.nullable(),
  player_id: nflmetaInteger.positive().nullable(), player_key: nflmetaText.nullable(),
  display_name: nflmetaText, position: nflmetaText.nullable(), position_group: nflmetaText.nullable(),
  resolved_player: z.boolean(), game_id: nflmetaInteger.positive(),
  season_year: nflmetaInteger, season_type: nflmetaText, week: nflmetaInteger.nullable(),
  round: nflmetaText.nullable(), game_date: nflmetaDate.nullable(),
  team_abbr: nflmetaText, opponent_abbr: nflmetaText, home_away: nflmetaText,
  result: z.enum(['W', 'L', 'T']).nullable(), rank: nflmetaInteger.positive(),
  stat_value: z.number().finite(),
}).passthrough().superRefine((row, ctx) => {
  for (const key of NFLMETA_BASE_STATS) {
    if ((row.stat_status[key] === 'reported') !== (row[key] !== null)) {
      ctx.addIssue({ code: 'custom', path: [key], message: 'Reported requires numeric input; other statuses require null' });
    }
  }
  if (row.resolved_player && (row.player_key === null || row.player_id === null)) {
    ctx.addIssue({ code: 'custom', path: ['resolved_player'], message: 'Resolved identity requires provider IDs' });
  }
});

export const nflmetaPlayerGamePageSchema = z.object({
  data: z.array(rowSchema).max(1000),
  meta: z.object({
    contract_version: z.literal('2'), missing_stat_policy: z.literal('null_with_stat_status'),
    stat_version_semantics: z.literal('player_game_content_sha256_not_a_sequence'),
    boxscore_updated_at_semantics: z.literal('latest_contributing_boxscore_row_write_not_correction_time'),
    correction_history_available: z.literal(false),
    total: nflmetaInteger, limit: nflmetaInteger.positive().max(1000), offset: nflmetaInteger,
    returned: nflmetaInteger, has_more: z.boolean(), season_year: nflmetaInteger,
    season_type: nflmetaText, stat: z.enum([...NFLMETA_BASE_STATS, ...derivedStats]),
    order: z.enum(['asc', 'desc']), filters: z.record(z.unknown()), coverage_note: z.string(),
  }).passthrough(),
}).passthrough().superRefine(({ data, meta }, ctx) => {
  const fail = (message: string) => ctx.addIssue({ code: 'custom', message });
  if (meta.returned !== data.length || data.length > meta.limit || meta.offset + data.length > meta.total) fail('Invalid page census');
  if (meta.has_more !== (meta.offset + data.length < meta.total)) fail('Invalid continuation flag');
  const seen = new Set<string>();
  for (const row of data) {
    if (row.season_year !== meta.season_year || row.season_type !== meta.season_type) fail('Row/query season mismatch');
    // Do not join unresolved players by name; no duplicate check can establish their identity.
    if (row.resolved_player) {
      const key = JSON.stringify([row.player_key, row.game_id, row.season_type]);
      if (seen.has(key)) fail('Duplicate resolved player-game');
      seen.add(key);
    }
    if (NFLMETA_BASE_STATS.includes(meta.stat as NflmetaBaseStat)) {
      const key = meta.stat as NflmetaBaseStat;
      if (row.stat_status[key] !== 'reported' || row[key] !== row.stat_value) fail('Selected statistic is missing or inconsistent');
    } else {
      const key = meta.stat as keyof typeof ratios;
      const [numerator, denominator] = ratios[key];
      if (row.stat_status[numerator] !== 'reported' || row.stat_status[denominator] !== 'reported'
        || row[denominator] === null || row[denominator] <= 0 || row[numerator] === null
        || row[key] === undefined || row[key] !== row.stat_value) fail('Unavailable or inconsistent selected rate');
      else {
        const expected = row[numerator]! / row[denominator]!;
        // Explicit TIBER synthetic acceptance tolerance; real provider precision remains unqualified.
        if (Math.abs(row.stat_value - expected) > 1e-6 * Math.max(1, Math.abs(expected))
          || (key.endsWith('_pct') && (row.stat_value < 0 || row.stat_value > 1))) {
          fail('Selected rate contradicts its reported inputs or fractional units');
        }
      }
    }
  }
});

/** No transport, storage, promotion, finality inference or full-game census. */
export function decodeSyntheticNflmetaPlayerGames(input: unknown, receipt: unknown) {
  const page = structuredClone(nflmetaPlayerGamePageSchema.parse(input));
  return {
    evidence: nflmetaSyntheticEvidence(receipt),
    endpoint: '/api/v1/stats/players/games' as const,
    query: page.meta,
    population: 'filtered_ranked_page_not_participation_census' as const,
    absentPlayerMeaning: 'unknown' as const,
    correctionHistory: 'unavailable' as const,
    rows: page.data.map(row => ({
      providerRow: row,
      factBasis: 'provider_reported_unverified' as const,
      kickoffAt: null,
      providerWriteAt: row.boxscore_updated_at,
      contentFingerprint: row.stat_version,
      finality: 'unknown' as const,
    })),
  };
}
