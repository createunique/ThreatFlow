import React from 'react';
import { Box, Tabs, Tab, Typography, Button, Chip, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { ChevronDown } from 'lucide-react';
import RawJsonModal from './RawJsonModal';

type ResultTabsProps = {
  data: any; // use your ResultNodeData / response type here
};

export default function ResultTabs({ data }: ResultTabsProps) {
  const [tab, setTab] = React.useState(0);
  const [openRaw, setOpenRaw] = React.useState(false);

  const summary = React.useMemo(() => {
    if (!data) return {};
    // Try to extract common fields safely; adapt to your backend shape
    return {
      score: data.score ?? data.meta?.score ?? null,
      verdict: data.verdict ?? data.meta?.verdict ?? null,
      detections: (data.detections || data.results || []).length || 0,
      type: data.file?.type ?? data.meta?.filetype ?? '',
      size: data.file?.size ?? data.meta?.filesize ?? null,
      timestamp: data.timestamp ?? data.meta?.time ?? null,
    };
  }, [data]);

  return (
    <Box>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} aria-label="Result tabs" variant="fullWidth" sx={{ mb: 1 }}>
        <Tab label="Summary" />
        <Tab label="Details" />
        <Tab label="Raw" />
      </Tabs>

      {tab === 0 && (
        <Box sx={{ px: 1 }}>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <Typography variant="subtitle2">Threat Score</Typography>
            {summary.score != null ? (
              <Chip label={summary.score} color={summary.score >= 75 ? 'error' : summary.score >= 40 ? 'warning' : 'success'} />
            ) : (
              <Chip label={summary.verdict ?? 'Unknown'} />
            )}
            <Box sx={{ flex: 1 }} />
            <Button size="small" onClick={() => setOpenRaw(true)}>View Full JSON</Button>
          </Box>

          <Typography variant="body2" color="text.secondary">Detections: {summary.detections}</Typography>
          <Typography variant="body2" color="text.secondary">File type: {summary.type || '—'}</Typography>
          {summary.size != null && <Typography variant="body2" color="text.secondary">Size: {(summary.size / 1024).toFixed(2)} KB</Typography>}
          {summary.timestamp && <Typography variant="caption" color="text.secondary">Analyzed: {new Date(summary.timestamp).toLocaleString()}</Typography>}
        </Box>
      )}

      {tab === 1 && (
        <Box sx={{ px: 1 }}>
          {/* Basic expandable sections. Replace keys with fields present in your result */}
          <Accordion>
            <AccordionSummary expandIcon={<ChevronDown />}>
              <Typography>Detections ({(data.detections || data.results || []).length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {(data.detections || data.results || []).map((d: any, i: number) => (
                <Box key={i} sx={{ mb: 1 }}>
                  <Typography variant="subtitle2">{d.name ?? d.rule ?? `Detection ${i + 1}`}</Typography>
                  <Typography variant="body2" color="text.secondary">{d.description ?? d.summary ?? JSON.stringify(d).slice(0, 200)}</Typography>
                </Box>
              ))}
              {(data.detections || data.results || []).length === 0 && <Typography variant="body2" color="text.secondary">No detections</Typography>}
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ChevronDown />}>
              <Typography>IOCs / Network</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {/* try to surface IPs, domains, hashes */}
              {(data.iocs || []).length ? (
                (data.iocs || []).map((ioc: any, idx: number) => (
                  <Typography key={idx} variant="body2">{ioc.type}: {ioc.value}</Typography>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">No IOCs extracted</Typography>
              )}
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {tab === 2 && (
        <Box sx={{ px: 1 }}>
          <Button size="small" onClick={() => setOpenRaw(true)}>Open Full JSON</Button>
          <Box component="pre" sx={{ maxHeight: 200, overflow: 'auto', fontSize: 12, mt: 1 }}>
            {JSON.stringify(data, null, 2)}
          </Box>
        </Box>
      )}

      <RawJsonModal open={openRaw} onClose={() => setOpenRaw(false)} json={data ?? {}} title="Analysis Result JSON" />
    </Box>
  );
}