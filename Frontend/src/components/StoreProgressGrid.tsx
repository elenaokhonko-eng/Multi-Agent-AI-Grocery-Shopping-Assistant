import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Store,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Loader2,
  ExternalLink,
  ShieldAlert,
  AlertCircle
} from 'lucide-react';

export interface StoreProgressInfo {
  state: string;
  progress: number;
  detail?: string;
  actionType?: string;
  resumeToken?: string;
}

interface StoreProgressGridProps {
  storeStates: Record<string, StoreProgressInfo>;
  onSolveChallenge?: (retailerId: string, resumeToken?: string) => void;
}

const STORE_CONFIG: Record<string, { name: string; color: string; badgeBg: string }> = {
  fairprice: {
    name: 'NTUC FairPrice',
    color: 'border-blue-500/30 dark:border-blue-500/20',
    badgeBg: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
  },
  shengsiong: {
    name: 'Sheng Siong',
    color: 'border-emerald-500/30 dark:border-emerald-500/20',
    badgeBg: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
  },
  littlefarms: {
    name: 'Little Farms',
    color: 'border-amber-500/30 dark:border-amber-500/20',
    badgeBg: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
  },
  redmart: {
    name: 'RedMart (Lazada)',
    color: 'border-rose-500/30 dark:border-rose-500/20',
    badgeBg: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20'
  },
};

export const StoreProgressGrid: React.FC<StoreProgressGridProps> = ({
  storeStates,
  onSolveChallenge,
}) => {
  const getStatusBadge = (info: StoreProgressInfo) => {
    switch (info.state) {
      case 'QUOTED':
        return (
          <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Quoted
          </Badge>
        );
      case 'PARTIAL':
        return (
          <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 font-medium">
            <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Partial Cart
          </Badge>
        );
      case 'USER_ACTION_REQUIRED':
        return (
          <Badge className="bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30 font-medium animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 mr-1" /> Action Required
          </Badge>
        );
      case 'FAILED':
        return (
          <Badge className="bg-destructive/15 text-destructive border-destructive/30 font-medium">
            <AlertCircle className="w-3.5 h-3.5 mr-1" /> Failed
          </Badge>
        );
      case 'QUEUED':
        return (
          <Badge variant="outline" className="text-muted-foreground font-normal">
            <Clock className="w-3.5 h-3.5 mr-1" /> Queued
          </Badge>
        );
      default:
        return (
          <Badge className="bg-primary/10 text-primary border-primary/20 font-medium">
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> {info.state.replace('_', ' ')}
          </Badge>
        );
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Object.entries(storeStates).map(([storeId, info]) => {
        const conf = STORE_CONFIG[storeId] || {
          name: storeId,
          color: 'border-border',
          badgeBg: 'bg-muted text-muted-foreground'
        };

        const isActionRequired = info.state === 'USER_ACTION_REQUIRED';
        const isFinished = ['QUOTED', 'PARTIAL', 'FAILED'].includes(info.state);

        return (
          <Card
            key={storeId}
            className={`border shadow-sm transition-all duration-200 bg-card/80 backdrop-blur-sm ${conf.color} ${
              isActionRequired ? 'ring-2 ring-rose-500/40 bg-rose-500/5' : ''
            }`}
          >
            <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
              <div className="flex items-center gap-2">
                <Store className="w-4 h-4 text-muted-foreground" />
                <CardTitle className="text-sm font-bold truncate">{conf.name}</CardTitle>
              </div>
              {getStatusBadge(info)}
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-3">
              {/* Progress Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Progress</span>
                  <span className="font-semibold">{info.progress}%</span>
                </div>
                <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 rounded-full ${
                      info.state === 'FAILED'
                        ? 'bg-destructive'
                        : isActionRequired
                        ? 'bg-rose-500'
                        : isFinished
                        ? 'bg-emerald-500'
                        : 'bg-primary'
                    }`}
                    style={{ width: `${Math.max(info.progress, 5)}%` }}
                  />
                </div>
              </div>

              {/* Status Message */}
              <p className="text-xs text-muted-foreground line-clamp-2 min-h-[32px]">
                {info.detail || (isFinished ? 'Execution finished' : 'Processing items...')}
              </p>

              {/* Action Button for User Action / Challenge */}
              {isActionRequired && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => onSolveChallenge?.(storeId, info.resumeToken)}
                  className="w-full text-xs h-8 shadow-sm"
                >
                  <ExternalLink className="w-3.5 h-3.5 mr-1" />
                  Solve Challenge in Browser
                </Button>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
