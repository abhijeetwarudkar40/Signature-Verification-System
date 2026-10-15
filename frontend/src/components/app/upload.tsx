import { ImagePlus, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { validateImage } from "@/lib/api";
import { cn } from "@/lib/utils";

function usePreviews(files: File[]) {
  const urls = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => urls.forEach((u) => URL.revokeObjectURL(u)), [urls]);
  return urls;
}

export function ImageDropzone({
  files,
  onChange,
  multiple = false,
  disabled,
}: {
  files: File[];
  onChange: (files: File[]) => void;
  multiple?: boolean;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [drag, setDrag] = useState(false);
  const previews = usePreviews(files);

  const add = (list: FileList | null) => {
    if (!list) return;
    const incoming = Array.from(list);
    const errs: string[] = [];
    const ok = incoming.filter((f) => {
      const e = validateImage(f);
      if (e) errs.push(e);
      return !e;
    });
    setErrors(errs);
    onChange(multiple ? [...files, ...ok] : ok.slice(0, 1));
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          if (!disabled) add(e.dataTransfer.files);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed p-8 text-center transition-colors",
          drag ? "border-primary bg-primary-soft" : "hover:border-primary/50",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        <ImagePlus className="h-8 w-8 text-primary" strokeWidth={1.5} />
        <p className="mt-3 font-medium">
          {multiple ? "Drop signature images or click to browse" : "Drop a signature image or click to browse"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">PNG or JPEG · up to 5 MB each</p>
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg"
          multiple={multiple}
          className="hidden"
          onChange={(e) => {
            add(e.target.files);
            e.target.value = "";
          }}
        />
      </div>
      {errors.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-destructive">
          {errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}
      {files.length > 0 && (
        <div className={cn("mt-4 grid gap-3", multiple ? "grid-cols-2 sm:grid-cols-3 xl:grid-cols-4" : "grid-cols-1")}>
          {files.map((f, i) => (
            <div key={`${f.name}-${i}`} className="group relative overflow-hidden rounded-lg border bg-card">
              <img src={previews[i]} alt={`Signature preview ${i + 1}`} className={cn("w-full object-contain p-2", multiple ? "h-28" : "h-56")} />
              <p className="truncate border-t px-2 py-1.5 text-xs text-muted-foreground">{f.name}</p>
              {!disabled && (
                <button
                  type="button"
                  aria-label={`Remove ${f.name}`}
                  onClick={() => onChange(files.filter((_, j) => j !== i))}
                  className="absolute right-1.5 top-1.5 rounded-full bg-card p-1 shadow-card hover:text-destructive"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
