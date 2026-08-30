import React, { useState } from 'react';
import { api } from '@/services/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  ShieldAlert,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Play
} from 'lucide-react';

interface ChallengeActionPanelProps {
  runId: string;
  retailerId: string;
  actionType?: string;
  resumeToken?: string;
  message?: string;
  onResumeSuccess?: () => void;
  onDismiss?: () => void;
}

export const ChallengeActionPanel: React.FC<ChallengeActionPanelProps> = ({
  runId,
  retailerId,
  actionType = 'LOGIN_REQUIRED',
  resumeToken: initialResumeToken = '',
  message,
  onResumeSuccess,
  onDismiss,
}) => {
  const { toast } = useToast();
  const [tokenInput, setTokenInput] = useState(initialResumeToken);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isResuming, setIsResuming] = useState(false);

  const handleLaunchHeaded = async () => {
    try {
      setIsLaunching(true);
      await api.launchRetailerSession(retailerId);
      toast({
        title: 'Browser Launched',
        description: `Headed browser profile opened for ${retailerId}. Complete your login or verification, then resume.`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to launch browser session';
      toast({
        title: 'Launch Failed',
        description: msg,
        variant: 'destructive',
      });
    } finally {
      setIsLaunching(false);
    }
  };

  const handleResume = async () => {
    if (!tokenInput.trim()) return;
    try {
      setIsResuming(true);
      await api.resumeRetailerSession(runId, retailerId, tokenInput.trim());
      toast({
        title: 'Worker Resumed',
        description: `Sent resume signal for ${retailerId}. Worker will verify session and proceed.`,
      });
      onResumeSuccess?.();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to resume session';
      toast({
        title: 'Resume Failed',
        description: msg,
        variant: 'destructive',
      });
    } finally {
      setIsResuming(false);
    }
  };

  return (
    <Card className="border-rose-500/40 bg-rose-500/5 shadow-lg backdrop-blur-md rounded-2xl overflow-hidden animate-in fade-in slide-in-from-top-4 duration-300">
      <CardHeader className="p-5 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-600 dark:text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-foreground">
                Action Required for {retailerId.toUpperCase()}
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                {actionType === 'LOGIN_REQUIRED' ? 'Authentication Required' : 'Security Challenge / CAPTCHA'}
              </CardDescription>
            </div>
          </div>
          <Badge className="bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30 text-xs">
            {actionType}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-5 pt-2 space-y-4">
        <p className="text-xs text-muted-foreground">
          {message ||
            `The ${retailerId} worker encountered an authentication prompt or CAPTCHA. Please open the persistent browser profile, complete the challenge, and resume.`}
        </p>

        <div className="p-3 bg-background/60 rounded-xl border border-border/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold text-foreground">1. Open Headed Browser Window</div>
            <div className="text-[11px] text-muted-foreground">
              Launches local Playwright persistent profile (sandboxed).
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleLaunchHeaded}
            disabled={isLaunching}
            className="text-xs h-8 border-border hover:bg-muted"
          >
            {isLaunching ? <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" /> : <ExternalLink className="w-3.5 h-3.5 mr-1" />}
            Launch Browser Session
          </Button>
        </div>

        <div className="space-y-2">
          <div className="text-xs font-semibold text-foreground">2. Enter Resume Token & Continue</div>
          <div className="flex gap-2">
            <Input
              placeholder="e.g. tok_fairprice_12345"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              className="bg-background text-xs font-mono"
            />
            <Button
              size="sm"
              onClick={handleResume}
              disabled={isResuming || !tokenInput.trim()}
              className="bg-rose-600 hover:bg-rose-700 text-white text-xs px-4"
            >
              {isResuming ? <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Play className="w-3.5 h-3.5 mr-1" />}
              Resume Worker
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
