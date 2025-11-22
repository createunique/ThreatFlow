/**
 * Skeleton Components
 * Professional loading placeholders for better UX
 */

import React from 'react';
import {
  Box,
  Skeleton,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
} from '@mui/material';

// Node Skeleton for Canvas Loading
export const NodeSkeleton: React.FC<{ width?: number; height?: number }> = ({
  width = 280,
  height = 200,
}) => (
  <Paper
    elevation={2}
    sx={{
      padding: 2,
      width,
      height,
      border: '1px solid #e0e0e0',
      borderRadius: 2,
      backgroundColor: '#fff',
    }}
  >
    <Skeleton variant="rectangular" width="100%" height={24} sx={{ mb: 2 }} />
    <Skeleton variant="rectangular" width="100%" height={120} />
    <Box sx={{ mt: 2 }}>
      <Skeleton variant="text" width="60%" />
      <Skeleton variant="text" width="40%" />
    </Box>
  </Paper>
);

// Workflow Canvas Skeleton
export const CanvasSkeleton: React.FC = () => (
  <Box sx={{ width: '100%', height: '100%', p: 2 }}>
    <Grid container spacing={2}>
      {Array.from({ length: 6 }).map((_, index) => (
        <Grid item key={index}>
          <NodeSkeleton />
        </Grid>
      ))}
    </Grid>
  </Box>
);

// Sidebar Skeleton
export const SidebarSkeleton: React.FC = () => (
  <Box sx={{ width: 280, p: 2 }}>
    <Skeleton variant="rectangular" width="100%" height={40} sx={{ mb: 2 }} />
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {Array.from({ length: 5 }).map((_, index) => (
        <Card key={index} elevation={1}>
          <CardContent sx={{ p: 2 }}>
            <Skeleton variant="rectangular" width="100%" height={20} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
          </CardContent>
        </Card>
      ))}
    </Box>
  </Box>
);

// Properties Panel Skeleton
export const PropertiesSkeleton: React.FC = () => (
  <Paper
    elevation={2}
    sx={{
      width: 280,
      height: '100%',
      padding: 2,
      backgroundColor: '#fafafa',
    }}
  >
    <Skeleton variant="rectangular" width="100%" height={32} sx={{ mb: 2 }} />
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {Array.from({ length: 4 }).map((_, index) => (
        <Box key={index}>
          <Skeleton variant="text" width="40%" sx={{ mb: 1 }} />
          <Skeleton variant="rectangular" width="100%" height={40} />
        </Box>
      ))}
    </Box>
  </Paper>
);

// Status Monitor Skeleton
export const StatusMonitorSkeleton: React.FC = () => (
  <Paper
    elevation={2}
    sx={{
      padding: 2,
      minWidth: 400,
      border: '1px solid #e0e0e0',
      borderRadius: 2,
    }}
  >
    <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
      <Skeleton variant="rectangular" width={150} height={24} />
      <Skeleton variant="rectangular" width={80} height={24} />
    </Box>
    <Skeleton variant="text" width="60%" sx={{ mb: 1 }} />
    <Skeleton variant="rectangular" width="100%" height={8} sx={{ mb: 2 }} />
    <Skeleton variant="rectangular" width="100%" height={80} />
  </Paper>
);

// Generic Content Skeleton
export const ContentSkeleton: React.FC<{
  lines?: number;
  width?: string | number;
  height?: string | number;
}> = ({ lines = 3, width = '100%', height = 20 }) => (
  <Box>
    {Array.from({ length: lines }).map((_, index) => (
      <Skeleton
        key={index}
        variant="text"
        width={width}
        height={height}
        sx={{ mb: 1 }}
      />
    ))}
  </Box>
);

// Table Skeleton
export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4,
}) => (
  <Box>
    {/* Header */}
    <Box sx={{ display: 'flex', gap: 2, mb: 2, p: 1 }}>
      {Array.from({ length: columns }).map((_, index) => (
        <Skeleton key={index} variant="text" width={100} height={24} />
      ))}
    </Box>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <Box key={rowIndex} sx={{ display: 'flex', gap: 2, mb: 1, p: 1 }}>
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton key={colIndex} variant="text" width={100} height={20} />
        ))}
      </Box>
    ))}
  </Box>
);

// Loading Overlay Component
export const LoadingOverlay: React.FC<{
  loading: boolean;
  message?: string;
  children: React.ReactNode;
}> = ({ loading, message = 'Loading...', children }) => (
  <Box sx={{ position: 'relative' }}>
    {children}
    {loading && (
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10,
          borderRadius: 1,
        }}
      >
        <Skeleton variant="circular" width={40} height={40} sx={{ mb: 1 }} />
        <Typography variant="caption" color="text.secondary">
          {message}
        </Typography>
      </Box>
    )}
  </Box>
);

// Inline Loading Spinner
export const InlineLoader: React.FC<{
  size?: number;
  message?: string;
  color?: 'primary' | 'secondary' | 'inherit';
}> = ({ size = 20, message, color = 'primary' }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <Skeleton variant="circular" width={size} height={size} />
    {message && (
      <Typography variant="caption" color="text.secondary">
        {message}
      </Typography>
    )}
  </Box>
);

export default {
  NodeSkeleton,
  CanvasSkeleton,
  SidebarSkeleton,
  PropertiesSkeleton,
  StatusMonitorSkeleton,
  ContentSkeleton,
  TableSkeleton,
  LoadingOverlay,
  InlineLoader,
};