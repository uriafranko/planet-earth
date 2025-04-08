
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import LoadingSpinner from '@/components/LoadingSpinner';

const Index: React.FC = () => {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading) {
      // If user is logged in, redirect to dashboard, otherwise to login
      if (user) {
        navigate('/dashboard');
      } else {
        navigate('/login');
      }
    }
  }, [user, isLoading, navigate]);

  // Show loading indicator while checking auth state
  return (
    <div className="min-h-screen flex items-center justify-center bg-space-gradient">
      <LoadingSpinner size="lg" />
    </div>
  );
};

export default Index;
