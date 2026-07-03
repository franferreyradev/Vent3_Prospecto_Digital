import Button from './Button';

interface PDFViewerProps {
  url: string;
  fileName?: string;
  allowDownload?: boolean;
}

export default function PDFViewer({ url, fileName, allowDownload = true }: PDFViewerProps) {
  return (
    <div className="flex max-w-prospecto flex-col gap-3">
      <div className="h-[600px] w-full overflow-hidden rounded-md border border-vent3-border">
        <iframe src={url} className="h-full w-full" title={fileName ?? 'Prospecto'} />
      </div>
      {allowDownload && (
        <a href={url} download className="self-start">
          <Button variant="secondary">Descargar {fileName ?? 'prospecto'}</Button>
        </a>
      )}
    </div>
  );
}
