
import { Shield, ShieldAlert, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { User } from "@/types/models";

interface RoleIndicatorProps {
  role: User['role'];
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const RoleIndicator: React.FC<RoleIndicatorProps> = ({ 
  role,
  showLabel = true,
  size = 'md'
}) => {
  const roleConfig = {
    admin: {
      icon: ShieldAlert,
      label: "Admin",
      variant: "destructive" as const
    },
    user: {
      icon: ShieldCheck,
      label: "User",
      variant: "default" as const
    },
    viewer: {
      icon: Shield,
      label: "Viewer",
      variant: "secondary" as const
    }
  };

  const config = roleConfig[role];
  const Icon = config.icon;
  
  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className={sizeClasses[size]} />
      {showLabel && <span>{config.label}</span>}
    </Badge>
  );
};

export default RoleIndicator;
