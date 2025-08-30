/**
 * Audio diagnostics helpers to verify recorded audio has valid content before sending to API.
 * Uses WebAudio API with <audio> element fallback for duration.
 */

export interface AudioDiagnostics {
  mimeType: string;
  sizeBytes: number;
  durationSec: number;
  sampleRate?: number;
  channels?: number;
  rms?: number;
  peak?: number;
  isSilent: boolean;
  decodingMethod: 'webaudio' | 'audio-element' | 'size-only';
}

async function getDurationViaAudioElement(blob: Blob): Promise<number> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio();
    const done = (val: number) => {
      URL.revokeObjectURL(url);
      resolve(val);
    };
    audio.onloadedmetadata = () => done(isFinite(audio.duration) ? audio.duration : 0);
    audio.onerror = () => done(0);
    audio.src = url;
    audio.load();
  });
}

export async function analyzeAudioBlob(
  blob: Blob,
  {
    minDuration = 0.3,
    minRms = 0.005
  }: { minDuration?: number; minRms?: number } = {}
): Promise<AudioDiagnostics> {
  const baseDiag: AudioDiagnostics = {
    mimeType: blob.type || 'application/octet-stream',
    sizeBytes: blob.size || 0,
    durationSec: 0,
    isSilent: true,
    decodingMethod: 'size-only'
  };

  if (!blob.size || blob.size < 512) {
    return baseDiag;
  }

  try {
    const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
    if (AudioCtx) {
      const ctx = new AudioCtx();
      const buffer = await new Promise<AudioBuffer>((resolve, reject) => {
        blob.arrayBuffer()
          .then((ab) => {
            const p = ctx.decodeAudioData(ab as ArrayBuffer, resolve, reject);
            if (p && typeof (p as any).then === 'function') {
              (p as Promise<AudioBuffer>).then(resolve).catch(reject);
            }
          })
          .catch(reject);
      });

      const channels = buffer.numberOfChannels || 1;
      const sampleRate = buffer.sampleRate;
      const duration = buffer.duration || 0;

      let sumSquares = 0;
      let count = 0;
      let peak = 0;

      for (let ch = 0; ch < channels; ch++) {
        const data = buffer.getChannelData(ch);
        const len = data.length;
        for (let i = 0; i < len; i += 64) {
          const v = data[i];
          const av = Math.abs(v);
          if (av > peak) peak = av;
          sumSquares += v * v;
          count++;
        }
      }

      const rms = count > 0 ? Math.sqrt(sumSquares / count) : 0;
      const isSilent = duration < minDuration || rms < minRms;

      return {
        ...baseDiag,
        durationSec: duration,
        sampleRate,
        channels,
        rms,
        peak,
        isSilent,
        decodingMethod: 'webaudio'
      };
    }
  } catch {
    // fall back below
  }

  try {
    const duration = await getDurationViaAudioElement(blob);
    const isSilent = duration < minDuration;
    return {
      ...baseDiag,
      durationSec: duration,
      isSilent,
      decodingMethod: 'audio-element'
    };
  } catch {
    return baseDiag;
  }
}

export async function logAudioDiagnostics(
  blob: Blob,
  options?: { minDuration?: number; minRms?: number }
): Promise<AudioDiagnostics> {
  const diag = await analyzeAudioBlob(blob, options);
  console.log('🎧 Audio Diagnostics:');
  console.log('  - mimeType:', diag.mimeType);
  console.log('  - sizeBytes:', diag.sizeBytes);
  console.log('  - durationSec:', Number.isFinite(diag.durationSec) ? diag.durationSec.toFixed(3) : diag.durationSec);
  if (diag.decodingMethod === 'webaudio') {
    console.log('  - sampleRate:', diag.sampleRate);
    console.log('  - channels:', diag.channels);
    console.log('  - rms:', diag.rms);
    console.log('  - peak:', diag.peak);
  }
  console.log('  - decodingMethod:', diag.decodingMethod);
  console.log('  - isSilent:', diag.isSilent);

  (blob as any).diagnostics = diag;
  return diag;
}

export async function validateAudioBeforeUpload(
  blob: Blob,
  {
    minSizeBytes = 2048,
    minDuration = 0.3,
    minRms = 0.005
  }: { minSizeBytes?: number; minDuration?: number; minRms?: number } = {}
): Promise<{ ok: boolean; diagnostics: AudioDiagnostics; reason?: string }> {
  const diag = await analyzeAudioBlob(blob, { minDuration, minRms });

  // New: explicit zero-size blob handling for clearer diagnosis
  if (diag.sizeBytes === 0) {
    return {
      ok: false,
      diagnostics: diag,
      reason: 'Không có dữ liệu audio (blob rỗng). Có thể MediaRecorder không sinh dữ liệu hoặc track bị muted.'
    };
  }

  if (diag.sizeBytes < minSizeBytes) {
    return { ok: false, diagnostics: diag, reason: `Audio quá nhỏ (${diag.sizeBytes} bytes)` };
  }
  if (diag.durationSec < minDuration) {
    return { ok: false, diagnostics: diag, reason: `Thời lượng quá ngắn (${diag.durationSec.toFixed(2)}s)` };
  }
  if (diag.decodingMethod === 'webaudio' && (diag.rms ?? 0) < minRms) {
    return { ok: false, diagnostics: diag, reason: `Âm lượng quá nhỏ (RMS=${diag.rms?.toFixed(4)})` };
  }
  return { ok: true, diagnostics: diag };
}