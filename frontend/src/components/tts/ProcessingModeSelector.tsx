import React from 'react';
import { Zap, Layers, Wand2 } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import type { ProcessingMode } from '../../hooks/useProcessingMode';

interface ProcessingModeSelectorProps {
  mode: ProcessingMode;
  onModeChange: (mode: ProcessingMode) => void;
  textLength?: number;
}

export default function ProcessingModeSelector({ 
  mode, 
  onModeChange,
  textLength = 0
}: ProcessingModeSelectorProps) {
  
  const modes: Array<{
    value: ProcessingMode;
    label: string;
    description: string;
    icon: React.ReactNode;
    recommended?: boolean;
  }> = [
    {
      value: 'auto',
      label: 'Auto',
      description: 'Automatically choose based on text length (> 3000 chars = Long Text)',
      icon: <Wand2 className="w-4 h-4" />,
      recommended: true
    },
    {
      value: 'streaming',
      label: 'Streaming',
      description: 'Real-time streaming for any text length (best for shorter texts)',
      icon: <Zap className="w-4 h-4" />
    },
    {
      value: 'long-text',
      label: 'Long Text',
      description: 'Background processing for any text length (best for longer texts)',
      icon: <Layers className="w-4 h-4" />
    }
  ];

  // Show what auto mode would choose
  const autoModeChoice = textLength > 3000 ? 'Long Text' : 'Streaming';

  return (
    <Card className="border-border/50">
      <CardContent className="p-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">Processing Mode</h3>
            {mode === 'auto' && textLength > 0 && (
              <span className="text-xs text-muted-foreground">
                Auto → {autoModeChoice}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 gap-2">
            {modes.map((modeOption) => (
              <button
                key={modeOption.value}
                onClick={() => {
                  console.log('[ProcessingModeSelector] User selected mode:', modeOption.value);
                  onModeChange(modeOption.value);
                }}
                className={`
                  relative flex items-start gap-3 p-3 rounded-lg border-2 transition-all duration-200 text-left
                  ${mode === modeOption.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50 hover:bg-accent/50'
                  }
                `}
              >
                <div className={`
                  flex items-center justify-center w-8 h-8 rounded-md shrink-0
                  ${mode === modeOption.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                  }
                `}>
                  {modeOption.icon}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-sm font-medium ${
                      mode === modeOption.value ? 'text-foreground' : 'text-foreground'
                    }`}>
                      {modeOption.label}
                    </span>
                    {modeOption.recommended && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {modeOption.description}
                  </p>
                </div>

                {mode === modeOption.value && (
                  <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary animate-pulse" />
                )}
              </button>
            ))}
          </div>

          {/* Info about current selection */}
          <div className="pt-2 border-t border-border/50">
            <p className="text-xs text-muted-foreground">
              {mode === 'auto' && (
                <>
                  <strong>Auto Mode:</strong> Text {textLength > 0 && `(${textLength} chars) `}
                  {textLength > 3000 ? 'will use Long Text mode' : 'will use Streaming mode'}
                  {textLength === 0 && 'will be automatically routed based on length'}
                </>
              )}
              {mode === 'streaming' && (
                <>
                  <strong>Streaming Mode:</strong> All text will use real-time streaming (regardless of length)
                </>
              )}
              {mode === 'long-text' && (
                <>
                  <strong>Long Text Mode:</strong> All text will use background processing (regardless of length)
                </>
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
