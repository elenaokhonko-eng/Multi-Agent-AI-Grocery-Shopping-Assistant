import { useState, useEffect, useRef } from 'react';
import { Search, ShoppingCart, User, Menu, Image, Mic, Camera, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import Tesseract from 'tesseract.js';
import { useSpeechToText } from '@/hooks/useSpeechToText';
import { useAudioLevel } from '@/hooks/useAudioLevel';
import VoiceCaptureUI from '@/components/VoiceCaptureUI';

export const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [cartCount] = useState(3);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  // multimodal state
  const [isOcrRunning, setIsOcrRunning] = useState(false);
  const [lastOcrText, setLastOcrText] = useState<string | null>(null);
  const [lastVoiceText, setLastVoiceText] = useState<string | null>(null);

  const { isSupported, isRecording, interim, finalText, start, stop, reset } =
    useSpeechToText({ lang: 'en-US', continuous: true });

  const { levels, isActive: levelActive, error: micErr, start: startLevel, stop: stopLevel } =
    useAudioLevel(24);

  // start/stop waveform stream in sync with speech recording
  useEffect(() => {
    if (isRecording) startLevel();
    else stopLevel();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRecording]);

  useEffect(() => {
    if (micErr) {
      // warn once if mic stream fails (still can record via Web Speech in some cases)
      console.warn('Mic level error:', micErr);
    }
  }, [micErr]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  // Scroll-based header visibility
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  const navigate = useNavigate();
  const { toast } = useToast();

  /* -------------------------- OCR handlers -------------------------- */
  const triggerImagePicker = () => fileInputRef.current?.click();
  const triggerCameraCapture = () => cameraInputRef.current?.click();

  const runOcrOnFile = async (file: File) => {
    if (!file) return;
    setIsOcrRunning(true);
    try {
      toast({ title: 'Reading image…', description: 'Running OCR on the selected image.' });
      const { data } = await Tesseract.recognize(file, 'eng');
      const text = (data.text || '').trim();
      if (text) {
        setLastOcrText(text);
        setSearchQuery(prev => (prev ? `${prev}\n${text}` : text));
        toast({ title: 'Text extracted', description: text.slice(0, 120) + (text.length > 120 ? '…' : '') });
      } else {
        toast({ title: 'No text found in image', variant: 'destructive' });
      }
    } catch (e) {
      console.error('OCR error', e);
      toast({ title: 'OCR failed', description: 'Could not read text from the image.', variant: 'destructive' });
    } finally {
      setIsOcrRunning(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (cameraInputRef.current) cameraInputRef.current.value = '';
    }
  };

  /* --------------------- Voice (Web Speech + UI) -------------------- */
  const toggleRecording = () => {
    if (!isSupported) {
      toast({
        title: 'Voice not supported',
        description: 'Use Chrome/Edge on HTTPS (or http://localhost).',
        variant: 'destructive',
      });
      return;
    }
    if (isRecording) {
      // Stop recording and capture the final transcription
      stop();
      const final = finalText.trim();
      if (final) {
        setSearchQuery(prev => (prev ? `${prev}\n${final}` : final));
        setLastVoiceText(final);
      }
      reset();
    } else {
      // Start recording
      start();
      toast({ title: 'Listening…', description: "Speak and I'll transcribe." });
    }
  };

  useEffect(() => {
    return () => {
      if (isRecording) {
        stop();
        stopLevel();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ----------------------------- Search ----------------------------- */
  const handleSearch = async () => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      toast({
        title: 'Search query required',
        description: "Please enter what you're looking for",
        variant: 'destructive',
      });
      return;
    }

    setIsSearching(true);

    try {
      const payload = {
        query: trimmed,
        modalities: {
          ocrText: lastOcrText || undefined,
          voiceText: lastVoiceText || undefined,
        },
      };

      const response = await fetch('http://localhost:3004/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      if (data.status === 'success') {
        navigate('/order-placement', {
          state: { searchResults: data.results, originalQuery: trimmed },
        });
        toast({
          title: 'Search completed!',
          description: `Found ${data.results.items_count} optimized items`,
        });
        setLastOcrText(null);
        setLastVoiceText(null);
      } else {
        toast({
          title: 'Search failed',
          description: data.message || 'An error occurred during search',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Search error:', error);
      toast({
        title: 'Connection error',
        description: 'Unable to connect to search service. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <header className={`header-auto-hide ${isHeaderVisible ? 'visible' : 'hidden'}`}>
      <div className="container mx-auto px-4">
        {/* Top Bar */}
        <div className="flex items-center justify-between py-2 text-sm border-b border-border">
          <div className="flex items-center space-x-6">
            <span className="text-muted-foreground">Save More on App</span>
            <span className="text-muted-foreground">Become a Seller</span>
            <span className="text-muted-foreground">Help & Support</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/orders" className="text-muted-foreground hover:text-primary">
              Track Orders
            </Link>
            <Button variant="ghost" size="sm">Login</Button>
            <Button variant="ghost" size="sm">Sign Up</Button>
          </div>
        </div>

        {/* Main Header */}
        <div className="flex items-center justify-between py-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">T</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                TitanStore
              </h1>
              <span className="text-xs text-accent font-medium">AI Powered</span>
            </div>
          </Link>

          {/* AI Chat Bar */}
          <div className="flex-1 max-w-2xl mx-8">
            <div className={`relative ai-search-container ${isSearchFocused || isSearchExpanded || searchQuery ? 'active' : ''}`}>
              {/* Neural network background pattern */}
              <div className="ai-neural-bg"></div>

              {/* Floating sparkles */}
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>

              <div className={`absolute left-3 z-10 transition-all duration-200 ${isSearchFocused || searchQuery ? 'top-4' : 'top-1/2 transform -translate-y-1/2'}`}>
                <Search className="h-5 w-5 text-muted-foreground" />
              </div>

              <Textarea
                placeholder="Ask AI anything - describe what you need..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchExpanded(e.target.value.length > 0);
                }}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                onKeyPress={handleKeyPress}
                disabled={isSearching}
                className={`pl-10 pr-32 py-3 text-base border-2 border-accent/20 focus:border-accent rounded-xl shadow-soft resize-none transition-all duration-300 ${isSearchFocused || isSearchExpanded || searchQuery ? 'min-h-[80px]' : 'min-h-[48px] overflow-hidden'}`}
                rows={isSearchFocused || isSearchExpanded || searchQuery ? 3 : 1}
              />

              {/* Actions */}
              <div className={`absolute right-2 z-10 flex space-x-1 transition-all duration-200 ${isSearchFocused || searchQuery ? 'top-3' : 'top-1/2 transform -translate-y-1/2'}`}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-accent/10"
                  onClick={triggerCameraCapture}
                  disabled={isOcrRunning || isSearching}
                  title="Capture from camera"
                >
                  {isOcrRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4 text-accent" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-accent/10"
                  onClick={triggerImagePicker}
                  disabled={isOcrRunning || isSearching}
                  title="Pick an image"
                >
                  {isOcrRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Image className="h-4 w-4 text-accent" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-8 w-8 p-0 hover:bg-accent/10 ${isRecording ? 'bg-red-50 ring-2 ring-red-300' : ''}`}
                  onClick={toggleRecording}
                  disabled={isSearching}
                  title={isRecording ? 'Stop voice' : 'Speak'}
                >
                  {isRecording ? <Loader2 className="h-4 w-4 animate-spin text-red-600" /> : <Mic className="h-4 w-4 text-accent" />}
                </Button>
                <Button
                  onClick={handleSearch}
                  disabled={isSearching || !searchQuery.trim()}
                  size="sm"
                  className="h-8 bg-gradient-primary text-white hover:opacity-90 disabled:opacity-50"
                >
                  {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* Helper / Interim transcript + Voice UI */}
            <div className={`transition-all duration-200 text-xs text-muted-foreground ml-10 ${isSearchFocused || searchQuery ? 'mt-2 opacity-100' : 'mt-1 opacity-70'}`}>
              <span className={`${isSearchFocused ? 'text-accent font-medium' : ''} transition-all duration-300`}>
                ✨ {isSearching ? (
                  <span className="animate-pulse">🤖 AI is analyzing your request...</span>
                ) : isSearchFocused ? (
                  <span>🧠 Advanced AI ready to find your perfect items</span>
                ) : (
                  'AI will help you find exactly what you\'re looking for'
                )}
              </span>
            </div>

            {isRecording && (
              <VoiceCaptureUI
                levels={levels}
                active={levelActive}
                interim={interim}
                onStop={toggleRecording}
              />
            )}
          </div>

          {/* Right Menu */}
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" className="flex items-center space-x-1">
              <User className="h-4 w-4" />
              <span className="hidden md:inline">Account</span>
            </Button>

            <Button variant="ghost" size="sm" className="relative flex items-center space-x-1">
              <ShoppingCart className="h-5 w-5" />
              <span className="hidden md:inline">Cart</span>
              {cartCount > 0 && (
                <Badge className="absolute -top-2 -right-2 h-5 w-5 text-xs bg-gradient-primary border-0">
                  {cartCount}
                </Badge>
              )}
            </Button>

            <Button variant="ghost" size="sm" className="md:hidden">
              <Menu className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Hidden inputs for images/camera (OCR) */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) runOcrOnFile(f);
        }}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) runOcrOnFile(f);
        }}
      />
    </header>
  );
};
