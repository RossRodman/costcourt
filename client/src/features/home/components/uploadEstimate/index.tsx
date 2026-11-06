import { Download, FileUp, LoaderCircle } from "lucide-react";
import { type DragEvent, useId, useState } from "react";

import { Alert } from "@/components/ui";
import { usePreviewEstimate } from "@/features/home/hooks";
import type { Estimate } from "@/types";
import { cn } from "@/utils/cn";

const TEMPLATE_URL = "/api/estimates/samples/warehouse-slab";
const MAX_BYTES = 1_000_000;

interface UploadEstimateProps {
  onLoaded: (estimate: Estimate) => void;
}

export function UploadEstimate({ onLoaded }: UploadEstimateProps) {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const preview = usePreviewEstimate();

  async function load(file: File | undefined) {
    if (!file) return;

    setFileError(null);
    preview.reset();

    if (file.size > MAX_BYTES) {
      setFileError("The file is larger than 1 MB.");
      return;
    }

    let data: unknown;

    try {
      data = JSON.parse(await file.text());
    } catch {
      setFileError(`${file.name} is not valid JSON.`);
      return;
    }

    preview.mutate(data, { onSuccess: onLoaded });
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    void load(event.dataTransfer.files[0]);
  }

  const error = fileError ?? (preview.error ? preview.error.message : null);

  return (
    <div className="space-y-3">
      <label
        htmlFor={inputId}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed px-6 py-10 text-center transition-colors",
          dragging ? "border-judge bg-judge/5" : "border-line hover:border-ink-faint",
        )}
      >
        {preview.isPending ? (
          <LoaderCircle className="size-6 animate-spin text-judge" aria-hidden />
        ) : (
          <FileUp className="size-6 text-ink-muted" aria-hidden />
        )}

        <span className="text-sm">
          <span className="font-medium text-judge">Choose a JSON file</span> or drop it here
        </span>
        <span className="text-xs text-ink-faint">Line items, quantities, rates and markups</span>

        <input
          id={inputId}
          type="file"
          accept="application/json,.json"
          className="sr-only"
          onChange={(event) => {
            void load(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </label>

      {error && <Alert title="This estimate can't be used">{error}</Alert>}

      <a
        href={TEMPLATE_URL}
        download="costcourt-estimate-template.json"
        className="inline-flex items-center gap-1.5 text-xs text-ink-muted hover:text-ink"
      >
        <Download className="size-3.5" aria-hidden />
        Download an example to see the format
      </a>
    </div>
  );
}
