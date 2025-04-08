
import React from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-space-gradient">
      <div className="text-center max-w-md space-y-6">
        <div className="flex flex-col items-center">
          <div className="cosmic-glow relative h-32 w-32 rounded-full bg-planet-primary flex items-center justify-center mb-8">
            <div className="h-28 w-28 rounded-full bg-planet-secondary/80 flex items-center justify-center">
              <span className="text-white font-bold text-5xl">404</span>
            </div>
            <div className="absolute top-0 right-4 h-4 w-4 rounded-full bg-planet-accent animate-ping" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Page Not Found</h1>
          <p className="text-muted-foreground mt-2 mb-6">
            The page you're looking for doesn't exist or has been moved.
          </p>
          <Button onClick={() => navigate('/dashboard')} size="lg">
            Return to Dashboard
          </Button>
        </div>
      </div>
      
      {/* Stars in background */}
      {Array.from({ length: 50 }).map((_, i) => {
        const size = Math.random() * 3 + 1;
        return (
          <div
            key={i}
            className="star"
            style={{
              width: `${size}px`,
              height: `${size}px`,
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
            }}
          />
        );
      })}
    </div>
  );
};

export default NotFound;
