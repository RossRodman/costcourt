import { useState } from "react";
import { useNavigate } from "react-router";

import { Alert, Skeleton } from "@/components/ui";
import {
  DebateLauncher,
  type EstimateSource,
  EstimatePreview,
  HeroSection,
  RecentDebates,
  SamplePicker,
  SourceTabs,
  UploadEstimate,
} from "@/features/home/components";
import { useDemos, useSample, useSamples, useStartDebate } from "@/features/home/hooks";
import { useHealth } from "@/hooks/useHealth";
import { Styled } from "@/styled";
import type { DebateRequest, Estimate } from "@/types";

export function HomePage() {
  const navigate = useNavigate();
  const health = useHealth();
  const samples = useSamples();
  const demos = useDemos();
  const start = useStartDebate();

  const [source, setSource] = useState<EstimateSource>("samples");
  const [sampleId, setSampleId] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState<Estimate | null>(null);
  const [rounds, setRounds] = useState(2);

  const selectedSampleId = sampleId ?? samples.data?.[0]?.id ?? null;
  const sample = useSample(source === "samples" ? selectedSampleId : null);
  const estimate = source === "samples" ? (sample.data ?? null) : uploaded;

  const online = health.kind === "online";
  const llmReady = online && health.health.llm_configured;
  const canDemo =
    source === "samples" &&
    selectedSampleId !== null &&
    (demos.data ?? []).includes(selectedSampleId);

  function startDebate(demo: boolean) {
    const target: DebateRequest =
      source === "samples"
        ? { sample_id: selectedSampleId ?? "" }
        : { estimate: uploaded ?? undefined };

    start.mutate(
      { ...target, rounds, demo },
      { onSuccess: (debate) => navigate(`/debates/${debate.id}`) },
    );
  }

  return (
    <div className="space-y-14">
      <HeroSection />

      <section aria-labelledby="choose" className="space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="choose" className={Styled.SectionTitle}>
              1. Choose an estimate
            </h2>
            <p className={Styled.SectionDescription}>
              Each sample hides a few realistic mistakes. Can the panel find them?
            </p>
          </div>
          <SourceTabs value={source} onChange={setSource} />
        </div>

        {source === "upload" ? (
          <UploadEstimate onLoaded={setUploaded} />
        ) : samples.isError ? (
          <Alert title="Couldn't load the samples">Is the backend running on port 8000?</Alert>
        ) : (
          <SamplePicker
            samples={samples.data}
            demos={demos.data ?? []}
            selectedId={selectedSampleId}
            onSelect={setSampleId}
          />
        )}

        {source === "samples" && selectedSampleId && sample.isPending && (
          <Skeleton className="h-64" />
        )}
        {estimate && <EstimatePreview estimate={estimate} />}
      </section>

      <section aria-labelledby="start" className="space-y-5">
        <div>
          <h2 id="start" className={Styled.SectionTitle}>
            2. Start the debate
          </h2>
          <p className={Styled.SectionDescription}>
            More rounds mean deeper rebuttals, and more time and tokens.
          </p>
        </div>
        <DebateLauncher
          rounds={rounds}
          onRoundsChange={setRounds}
          canStart={Boolean(estimate) && llmReady}
          canDemo={canDemo}
          missingKey={online && !llmReady}
          pending={start.isPending}
          error={start.error?.message ?? null}
          onStart={startDebate}
        />
      </section>

      <RecentDebates />
    </div>
  );
}
