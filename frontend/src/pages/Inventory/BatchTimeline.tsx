/**
 * Batch Timeline Component
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * Description:
 *   Visual timeline showing batch journey through all stages
 *   - Vertical timeline with MUI Timeline component
 *   - Color-coded status indicators
 *   - Event details and timestamps
 */

import React from 'react';
import {
    Timeline,
    TimelineItem,
    TimelineSeparator,
    TimelineConnector,
    TimelineContent,
    TimelineDot,
    TimelineOppositeContent,
} from '@mui/lab';
import {
    Box,
    Typography,
    Paper,
    Chip,
} from '@mui/material';
import {
    CheckCircle as CompletedIcon,
    RadioButtonChecked as InProgressIcon,
    RadioButtonUnchecked as PendingIcon,
} from '@mui/icons-material';
import { BatchTimelineResponse } from '../../api/batchTracking';

interface BatchTimelineProps {
    timeline: BatchTimelineResponse;
}

export default function BatchTimeline({ timeline }: BatchTimelineProps) {
    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CompletedIcon />;
            case 'in_progress':
                return <InProgressIcon />;
            default:
                return <PendingIcon />;
        }
    };

    const getStatusColor = (status: string): "grey" | "inherit" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
        switch (status) {
            case 'completed':
                return 'success';
            case 'in_progress':
                return 'primary';
            default:
                return 'grey';
        }
    };

    return (
        <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
                Batch Journey Timeline
            </Typography>

            <Timeline position="right">
                {timeline.timeline.map((stage, index) => (
                    <TimelineItem key={index}>
                        <TimelineOppositeContent color="text.secondary" sx={{ flex: 0.3 }}>
                            {stage.timestamp ? (
                                <Typography variant="body2">
                                    {new Date(stage.timestamp).toLocaleString()}
                                </Typography>
                            ) : (
                                <Typography variant="body2" color="text.disabled">
                                    Pending
                                </Typography>
                            )}
                        </TimelineOppositeContent>

                        <TimelineSeparator>
                            <TimelineDot color={getStatusColor(stage.status)}>
                                {getStatusIcon(stage.status)}
                            </TimelineDot>
                            {index < timeline.timeline.length - 1 && <TimelineConnector />}
                        </TimelineSeparator>

                        <TimelineContent>
                            <Box sx={{ mb: 2 }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                    <Typography variant="h6" component="span">
                                        {stage.stage_name}
                                    </Typography>
                                    <Chip
                                        label={stage.status.replace('_', ' ').toUpperCase()}
                                        size="small"
                                        color={getStatusColor(stage.status)}
                                    />
                                </Box>

                                {stage.details && Object.keys(stage.details).length > 0 && (
                                    <Box sx={{ mt: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                                        {Object.entries(stage.details).map(([key, value]) => (
                                            <Typography key={key} variant="body2" color="text.secondary">
                                                <strong>{key.replace('_', ' ')}:</strong> {String(value)}
                                            </Typography>
                                        ))}
                                    </Box>
                                )}
                            </Box>
                        </TimelineContent>
                    </TimelineItem>
                ))}
            </Timeline>
        </Paper>
    );
}
