import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS,
  FORGE_WEEKLY_UPSTREAM_SCAFFOLD_DERIVED_SKILL_EXPORT_WEEKS,
  buildForgeWeeklyDerivedArtifactFromRawSources,
  buildForgeWeeklySkillDerivedArtifactFromRawSources,
  buildForgeWeeklySkillDerivedArtifactsForWeeks,
  forgeWeeklyPlayerInputArraySchema,
  getForgeWeeklySkillSupportedWeeksFromRawSources,
  getForgeWeeklySkillDerivedArtifactPath,
  getForgeWeeklyUpstreamScaffoldSkillDerivedArtifactPath,
  toDeterministicForgeWeeklyDerivedJson,
  toDeterministicForgeWeeklySampleJson,
  toDeterministicForgeWeeklySkillDerivedJson,
  writeForgeWeeklyDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifactsForWeeks,
  writeForgeWeeklyUpstreamScaffoldSkillDerivedArtifactsForWeeks,
} from '../src/index.js';

describe('forge weekly derived artifact export lanes', () => {
  it('builds a QB-only derived artifact that validates against ForgeWeeklyPlayerInput', () => {
    const artifact = buildForgeWeeklyDerivedArtifactFromRawSources();
    const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);

    expect(parsed).toHaveLength(2);
    expect(parsed.every((record) => record.position === 'QB')).toBe(true);
    expect(parsed.map((record) => record.playerId)).toEqual(['00-0033901', '00-0037183']);
  });

  it('builds broader skill-position artifacts for multiple weeks', () => {
    const artifacts = buildForgeWeeklySkillDerivedArtifactsForWeeks();
    const supportedWeeks = getForgeWeeklySkillSupportedWeeksFromRawSources({ season: 2024 });

    expect(supportedWeeks).toEqual([1, 2, 3, 4, 5, 6]);
    expect(artifacts.map((artifact) => artifact.week)).toEqual(supportedWeeks);

    for (const { season, week, artifact } of artifacts) {
      const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);
      expect(parsed).toHaveLength(8);
      expect([...new Set(parsed.map((record) => record.position))].sort()).toEqual([
        'QB',
        'RB',
        'TE',
        'WR',
      ]);
      expect(parsed.every((record) => record.season === season && record.week === week)).toBe(true);
      expect(parsed.every((record) => record.practiceParticipation === 'none')).toBe(true);
      expect(parsed.every((record) => record.opponentDefenseTier === 'neutral')).toBe(true);
      expect(parsed.every((record) => record.activeProjection === 1)).toBe(true);
      expect(parsed.every((record) => record.fantasyPointsPerOpportunity <= 3)).toBe(true);
      expect(parsed.every((record) => (record.qualityFlags ?? []).length === new Set(record.qualityFlags ?? []).size)).toBe(
        true,
      );
      expect(parsed.map((record) => record.playerId)).toEqual([
        '00-0033901',
        '00-0036976',
        '00-0037183',
        '00-0037834',
        '00-0038047',
        '00-0038122',
        '00-0038134',
        '00-0039152',
      ]);
    }
  });

  it('serializes week 6 audit players with cleaner semantic defaults', () => {
    const weekSix = buildForgeWeeklySkillDerivedArtifactFromRawSources({ season: 2024, week: 6 });
    const byName = new Map(weekSix.map((record) => [record.playerName, record]));

    const gibbs = byName.get('Jahmyr Gibbs');
    const stBrown = byName.get('Amon-Ra St. Brown');
    const goff = byName.get('Jared Goff');
    const robinson = byName.get('Bijan Robinson');
    const pitts = byName.get('Kyle Pitts');

    expect(gibbs?.activeProjection).toBe(1);
    expect(stBrown?.routeParticipation).toBeGreaterThan(0);
    expect(goff?.opponentDefenseTier).toBe('neutral');
    expect(robinson?.practiceParticipation).toBe('none');
    expect(new Set(weekSix.map((record) => record.roleVolatility)).size).toBeGreaterThan(1);
    expect(new Set(weekSix.map((record) => record.featureCoverage)).size).toBeGreaterThan(1);
    expect(gibbs?.qualityFlags).toContain(
      'role_volatility_derived_from_recent_opportunity_share_and_role_mix_changes',
    );
    expect(goff?.qualityFlags).toContain('routes_and_route_participation_not_available_set_to_0_for_qb_rows');
    expect(pitts?.qualityFlags).toContain(
      'routes_and_route_participation_approximated_from_team_pass_attempts_and_player_target_volume',
    );
  });

  it('uses fallback role-volatility defaults only when history is unavailable', () => {
    const weekOne = buildForgeWeeklySkillDerivedArtifactFromRawSources({ season: 2024, week: 1 });
    expect(weekOne.every((record) => record.roleVolatility === 0.5)).toBe(true);
    expect(
      weekOne.every((record) =>
        (record.qualityFlags ?? []).includes('role_volatility_defaulted_to_neutral_midpoint_due_to_missing_multigame_history'),
      ),
    ).toBe(true);

    const weekSix = buildForgeWeeklySkillDerivedArtifactFromRawSources({ season: 2024, week: 6 });
    expect(weekSix.some((record) => record.roleVolatility !== 0.5)).toBe(true);
    expect(
      weekSix.every((record) =>
        (record.qualityFlags ?? []).includes('role_volatility_derived_from_recent_opportunity_share_and_role_mix_changes'),
      ),
    ).toBe(true);
  });

  it('is deterministic and matches committed derived artifacts', () => {
    const firstQbPass = toDeterministicForgeWeeklyDerivedJson();
    const secondQbPass = toDeterministicForgeWeeklyDerivedJson();
    const committedQb = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH), 'utf-8');

    expect(firstQbPass).toEqual(secondQbPass);
    expect(firstQbPass).toEqual(committedQb);

    for (const week of FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS) {
      const firstSkillPass = toDeterministicForgeWeeklySkillDerivedJson({ week });
      const secondSkillPass = toDeterministicForgeWeeklySkillDerivedJson({ week });
      const committedSkill = readFileSync(
        path.resolve(getForgeWeeklySkillDerivedArtifactPath(2024, week)),
        'utf-8',
      );

      expect(firstSkillPass).toEqual(secondSkillPass);
      expect(firstSkillPass).toEqual(committedSkill);
    }
  });

  it('fails closed for missing week support in raw fixtures', () => {
    expect(() =>
      buildForgeWeeklySkillDerivedArtifactFromRawSources({
        season: 2024,
        week: 7,
      }),
    ).toThrow('No skill-position records found');
  });

  it('fails closed when multi-week export requests unsupported weeks', () => {
    expect(() =>
      buildForgeWeeklySkillDerivedArtifactsForWeeks({
        season: 2024,
        weeks: [1, 2, 7],
      }),
    ).toThrow('Requested unsupported skill-derived weeks (7)');
  });

  it('fails closed when source path is missing', () => {
    expect(() =>
      buildForgeWeeklySkillDerivedArtifactFromRawSources({
        playerStatsSourcePath: 'data/raw/does_not_exist.json',
      }),
    ).toThrow();
  });

  it('fails closed when source records are invalid for the selected slice', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-derived-invalid-'));
    const invalidPlayerStatsPath = path.join(tempRoot, 'weekly_player_stats.invalid.json');

    writeFileSync(
      invalidPlayerStatsPath,
      JSON.stringify(
        {
          provenance: 'test',
          source_path: FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH,
          records: [
            {
              player_id: '00-0033901',
              full_name: 'Jared Goff',
              position: 'QB',
              team: 'DET',
              season: 2024,
              week: 1,
              targets: -2,
              receptions: 0,
              receiving_yards: 0,
              rushing_attempts: 3,
              rushing_yards: 7,
              pass_attempts: 28,
              fantasy_points_ppr: 17.7,
            },
          ],
        },
        null,
        2,
      ),
      'utf-8',
    );

    expect(() =>
      buildForgeWeeklySkillDerivedArtifactFromRawSources({
        playerStatsSourcePath: invalidPlayerStatsPath,
      }),
    ).toThrow();
  });

  it('fixture-derived sample export remains available and deterministic', () => {
    const sampleJson = toDeterministicForgeWeeklySampleJson();
    expect(sampleJson).toContain('forge-weekly-input-fixtures-v1');
  });

  it('writes deterministic derived artifact files to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-derived-'));
    const qbOutputPath = path.join(tempRoot, 'qb.artifact.json');
    const skillOutputPath = path.join(tempRoot, 'skill.artifact.json');

    const writtenQb = writeForgeWeeklyDerivedArtifact(qbOutputPath);
    const writtenSkill = writeForgeWeeklySkillDerivedArtifact(skillOutputPath);

    const qbFileContents = readFileSync(writtenQb, 'utf-8');
    const skillFileContents = readFileSync(writtenSkill, 'utf-8');

    expect(writtenQb).toEqual(path.resolve(qbOutputPath));
    expect(writtenSkill).toEqual(path.resolve(skillOutputPath));
    expect(qbFileContents).toEqual(toDeterministicForgeWeeklyDerivedJson());
    expect(skillFileContents).toEqual(toDeterministicForgeWeeklySkillDerivedJson());
  });

  it('writes deterministic weekly skill artifacts for the configured week set', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-skill-multi-'));

    const outputPaths = writeForgeWeeklySkillDerivedArtifactsForWeeks(tempRoot);

    expect(outputPaths).toHaveLength(FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS.length);

    for (const week of FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS) {
      const basename = path.basename(getForgeWeeklySkillDerivedArtifactPath(2024, week));
      const outputPath = path.resolve(path.join(tempRoot, basename));
      const written = readFileSync(outputPath, 'utf-8');

      expect(outputPaths).toContain(outputPath);
      expect(written).toEqual(toDeterministicForgeWeeklySkillDerivedJson({ week }));
    }
  });

  it('keeps backward compatibility for the original skill artifact path', () => {
    const weekOneCommitted = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH), 'utf-8');
    expect(weekOneCommitted).toEqual(toDeterministicForgeWeeklySkillDerivedJson({ week: 1 }));
  });


  it('uses distinct artifact naming and deterministic week ordering for upstream scaffold lane', () => {
    expect(FORGE_WEEKLY_UPSTREAM_SCAFFOLD_DERIVED_SKILL_EXPORT_WEEKS).toEqual([1, 2, 3]);

    const weekThreePath = getForgeWeeklyUpstreamScaffoldSkillDerivedArtifactPath(2024, 3);
    expect(weekThreePath).toContain('skill_upstream_public_w01_w03_8player_scaffold.derived.json');
    expect(weekThreePath).not.toContain('skill_offline_fixture.derived.json');
  });

  it('writes upstream scaffold artifacts into separate filenames without overwriting legacy outputs', () => {
    const playerStats = {
      provenance: 'upstream_fixture_test',
      source_path: 'test/player_stats',
      records: [
        { player_id: '00-0033901', full_name: 'Jared Goff', position: 'QB', team: 'DET', season: 2024, week: 2, targets: 0, receptions: 0, receiving_yards: 0, rushing_attempts: 2, rushing_yards: 6, pass_attempts: 30, fantasy_points_ppr: 18.1 },
        { player_id: '00-0036976', full_name: 'Jahmyr Gibbs', position: 'RB', team: 'DET', season: 2024, week: 2, targets: 4, receptions: 3, receiving_yards: 28, rushing_attempts: 11, rushing_yards: 58, pass_attempts: 0, fantasy_points_ppr: 15.2 },
        { player_id: '00-0037183', full_name: 'Kirk Cousins', position: 'QB', team: 'ATL', season: 2024, week: 2, targets: 0, receptions: 0, receiving_yards: 0, rushing_attempts: 1, rushing_yards: 2, pass_attempts: 33, fantasy_points_ppr: 17.4 },
        { player_id: '00-0037834', full_name: 'Amon-Ra St. Brown', position: 'WR', team: 'DET', season: 2024, week: 2, targets: 10, receptions: 7, receiving_yards: 84, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 22.6 },
        { player_id: '00-0038047', full_name: 'Sam LaPorta', position: 'TE', team: 'DET', season: 2024, week: 2, targets: 7, receptions: 5, receiving_yards: 61, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 14.1 },
        { player_id: '00-0038122', full_name: 'Kyle Pitts', position: 'TE', team: 'ATL', season: 2024, week: 2, targets: 6, receptions: 4, receiving_yards: 49, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 10.9 },
        { player_id: '00-0038134', full_name: 'Bijan Robinson', position: 'RB', team: 'ATL', season: 2024, week: 2, targets: 5, receptions: 4, receiving_yards: 31, rushing_attempts: 15, rushing_yards: 70, pass_attempts: 0, fantasy_points_ppr: 21.3 },
        { player_id: '00-0039152', full_name: 'Drake London', position: 'WR', team: 'ATL', season: 2024, week: 2, targets: 9, receptions: 6, receiving_yards: 76, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 18.7 },
        { player_id: '00-0033901', full_name: 'Jared Goff', position: 'QB', team: 'DET', season: 2024, week: 1, targets: 0, receptions: 0, receiving_yards: 0, rushing_attempts: 2, rushing_yards: 5, pass_attempts: 28, fantasy_points_ppr: 16.6 },
        { player_id: '00-0036976', full_name: 'Jahmyr Gibbs', position: 'RB', team: 'DET', season: 2024, week: 1, targets: 5, receptions: 4, receiving_yards: 34, rushing_attempts: 10, rushing_yards: 54, pass_attempts: 0, fantasy_points_ppr: 16.2 },
        { player_id: '00-0037183', full_name: 'Kirk Cousins', position: 'QB', team: 'ATL', season: 2024, week: 1, targets: 0, receptions: 0, receiving_yards: 0, rushing_attempts: 1, rushing_yards: 1, pass_attempts: 31, fantasy_points_ppr: 16.9 },
        { player_id: '00-0037834', full_name: 'Amon-Ra St. Brown', position: 'WR', team: 'DET', season: 2024, week: 1, targets: 11, receptions: 8, receiving_yards: 96, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 24.5 },
        { player_id: '00-0038047', full_name: 'Sam LaPorta', position: 'TE', team: 'DET', season: 2024, week: 1, targets: 8, receptions: 6, receiving_yards: 72, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 15.3 },
        { player_id: '00-0038122', full_name: 'Kyle Pitts', position: 'TE', team: 'ATL', season: 2024, week: 1, targets: 5, receptions: 3, receiving_yards: 40, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 8.5 },
        { player_id: '00-0038134', full_name: 'Bijan Robinson', position: 'RB', team: 'ATL', season: 2024, week: 1, targets: 6, receptions: 5, receiving_yards: 37, rushing_attempts: 14, rushing_yards: 63, pass_attempts: 0, fantasy_points_ppr: 20.4 },
        { player_id: '00-0039152', full_name: 'Drake London', position: 'WR', team: 'ATL', season: 2024, week: 1, targets: 8, receptions: 5, receiving_yards: 68, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 16.1 },
        { player_id: '00-0033901', full_name: 'Jared Goff', position: 'QB', team: 'DET', season: 2024, week: 3, targets: 0, receptions: 0, receiving_yards: 0, rushing_attempts: 3, rushing_yards: 8, pass_attempts: 35, fantasy_points_ppr: 19.2 },
        { player_id: '00-0036976', full_name: 'Jahmyr Gibbs', position: 'RB', team: 'DET', season: 2024, week: 3, targets: 6, receptions: 5, receiving_yards: 41, rushing_attempts: 12, rushing_yards: 64, pass_attempts: 0, fantasy_points_ppr: 18.6 },
        { player_id: '00-0037183', full_name: 'Kirk Cousins', position: 'QB', team: 'ATL', season: 2024, week: 3, targets: 0, receptions: 0, receiving_yards: 0, rushing_attempts: 1, rushing_yards: 2, pass_attempts: 34, fantasy_points_ppr: 18.3 },
        { player_id: '00-0037834', full_name: 'Amon-Ra St. Brown', position: 'WR', team: 'DET', season: 2024, week: 3, targets: 12, receptions: 9, receiving_yards: 104, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 27.8 },
        { player_id: '00-0038047', full_name: 'Sam LaPorta', position: 'TE', team: 'DET', season: 2024, week: 3, targets: 6, receptions: 5, receiving_yards: 55, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 12.4 },
        { player_id: '00-0038122', full_name: 'Kyle Pitts', position: 'TE', team: 'ATL', season: 2024, week: 3, targets: 7, receptions: 5, receiving_yards: 63, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 13.6 },
        { player_id: '00-0038134', full_name: 'Bijan Robinson', position: 'RB', team: 'ATL', season: 2024, week: 3, targets: 4, receptions: 3, receiving_yards: 24, rushing_attempts: 16, rushing_yards: 73, pass_attempts: 0, fantasy_points_ppr: 19.1 },
        { player_id: '00-0039152', full_name: 'Drake London', position: 'WR', team: 'ATL', season: 2024, week: 3, targets: 10, receptions: 7, receiving_yards: 82, rushing_attempts: 0, rushing_yards: 0, pass_attempts: 0, fantasy_points_ppr: 19.9 },
      ],
    };

    const teamContext = {
      provenance: 'upstream_fixture_test',
      source_path: 'test/team_context',
      records: [
        { team: 'ATL', season: 2024, week: 2, team_pass_attempts: 34, team_rush_attempts: 27, team_points: 24 },
        { team: 'DET', season: 2024, week: 2, team_pass_attempts: 31, team_rush_attempts: 26, team_points: 28 },
        { team: 'ATL', season: 2024, week: 1, team_pass_attempts: 32, team_rush_attempts: 25, team_points: 20 },
        { team: 'DET', season: 2024, week: 1, team_pass_attempts: 30, team_rush_attempts: 24, team_points: 27 },
        { team: 'ATL', season: 2024, week: 3, team_pass_attempts: 35, team_rush_attempts: 26, team_points: 23 },
        { team: 'DET', season: 2024, week: 3, team_pass_attempts: 33, team_rush_attempts: 25, team_points: 30 },
      ],
    };

    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-upstream-skill-'));
    const playerPath = path.join(tempRoot, 'weekly_player_stats.upstream_fixture_test.json');
    const teamPath = path.join(tempRoot, 'team_week_context.upstream_fixture_test.json');

    writeFileSync(playerPath, `${JSON.stringify(playerStats, null, 2)}\n`, 'utf-8');
    writeFileSync(teamPath, `${JSON.stringify(teamContext, null, 2)}\n`, 'utf-8');

    const outputPaths = writeForgeWeeklyUpstreamScaffoldSkillDerivedArtifactsForWeeks(tempRoot, {
      playerStatsSourcePath: playerPath,
      teamContextSourcePath: teamPath,
      asOf: '2026-04-08T00:00:00Z',
    });

    expect(outputPaths).toHaveLength(3);

    const weeksFromFiles = outputPaths.map((outputPath) => Number(outputPath.match(/_w(\d{2})\./)?.[1] ?? '0'));
    expect(weeksFromFiles).toEqual([1, 2, 3]);
    expect(outputPaths.every((outputPath) => outputPath.includes('skill_upstream_public_w01_w03_8player_scaffold.derived.json'))).toBe(true);
    expect(outputPaths.every((outputPath) => !outputPath.includes('skill_offline_fixture.derived.json'))).toBe(true);
  });

  it('floors derived yardsPerCarry at 0 for negative rushing yards while preserving raw source values', () => {
    const playerStats = {
      provenance: 'upstream_fixture_test_negative_rush',
      source_path: 'test/player_stats_negative_rush',
      records: [
        {
          player_id: '00-0037183',
          full_name: 'Kirk Cousins',
          position: 'QB',
          team: 'ATL',
          season: 2024,
          week: 1,
          targets: 0,
          receptions: 0,
          receiving_yards: 0,
          rushing_attempts: 4,
          rushing_yards: -1,
          pass_attempts: 31,
          fantasy_points_ppr: 16.9,
        },
      ],
    };
    const teamContext = {
      provenance: 'upstream_fixture_test_negative_rush',
      source_path: 'test/team_context_negative_rush',
      records: [
        {
          team: 'ATL',
          season: 2024,
          week: 1,
          team_pass_attempts: 32,
          team_rush_attempts: 25,
          team_points: 20,
        },
      ],
    };

    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-negative-rush-'));
    const playerPath = path.join(tempRoot, 'weekly_player_stats.negative_rush.json');
    const teamPath = path.join(tempRoot, 'team_week_context.negative_rush.json');
    writeFileSync(playerPath, `${JSON.stringify(playerStats, null, 2)}\n`, 'utf-8');
    writeFileSync(teamPath, `${JSON.stringify(teamContext, null, 2)}\n`, 'utf-8');

    const artifact = buildForgeWeeklySkillDerivedArtifactFromRawSources({
      playerStatsSourcePath: playerPath,
      teamContextSourcePath: teamPath,
      season: 2024,
      week: 1,
    });

    expect(artifact).toHaveLength(1);
    expect(artifact[0]?.playerName).toBe('Kirk Cousins');
    expect(artifact[0]?.rushAttempts).toBe(4);
    expect(artifact[0]?.yardsPerCarry).toBe(0);

    const persistedRaw = JSON.parse(readFileSync(playerPath, 'utf-8')) as {
      records: Array<{ player_id: string; rushing_yards: number }>;
    };
    expect(persistedRaw.records[0]?.player_id).toBe('00-0037183');
    expect(persistedRaw.records[0]?.rushing_yards).toBe(-1);
  });
});
