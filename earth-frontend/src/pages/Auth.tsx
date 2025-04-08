
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ShieldAlert, ShieldCheck, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import Logo from '@/components/Logo';
import ThemeToggle from '@/components/ThemeToggle';
import LoadingSpinner from '@/components/LoadingSpinner';

const Auth: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // If user is already logged in, redirect to dashboard
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const success = await login(email, password);
      if (success) {
        navigate('/dashboard');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Add stars to the background
  const renderStars = () => {
    const stars = [];
    for (let i = 0; i < 50; i++) {
      const size = Math.random() * 3 + 1;
      stars.push(
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
    }
    return stars;
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-space-gradient">
      {renderStars()}
      
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      
      <div className="w-full max-w-md space-y-8 relative z-10">
        <div className="flex flex-col items-center space-y-2">
          <Logo size="lg" showText />
          <h1 className="text-xl font-medium mt-4">Welcome to Planet Earth Dashboard</h1>
          <p className="text-sm text-center text-muted-foreground max-w-xs">
            Explore and manage Earth data with our intuitive dashboard
          </p>
        </div>

        <Card className="glass-card cosmic-glow">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access the dashboard
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleLogin}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : <User className="h-4 w-4 mr-2" />}
                Sign In
              </Button>
              
              <div className="grid grid-cols-2 gap-2 w-full text-center text-xs text-muted-foreground">
                <div className="flex flex-col items-center p-2 border rounded-md">
                  <div className="flex items-center gap-1 font-medium mb-1">
                    <ShieldAlert className="h-3.5 w-3.5 text-destructive" />
                    Admin
                  </div>
                  <span>admin@planet-earth.com</span>
                  <span>admin123</span>
                </div>
                <div className="flex flex-col items-center p-2 border rounded-md">
                  <div className="flex items-center gap-1 font-medium mb-1">
                    <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                    User
                  </div>
                  <span>user@planet-earth.com</span>
                  <span>user123</span>
                </div>
              </div>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs text-muted-foreground py-2">
          &copy; {new Date().getFullYear()} Planet Earth Dashboard. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default Auth;
