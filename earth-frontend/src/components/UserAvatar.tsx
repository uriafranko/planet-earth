
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User } from "@/types/models";

interface UserAvatarProps {
  user: User;
  size?: "sm" | "md" | "lg";
  showStatus?: boolean;
}

const UserAvatar: React.FC<UserAvatarProps> = ({ user, size = "md", showStatus = false }) => {
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
  };
  
  const statusSizeClasses = {
    sm: "h-2 w-2",
    md: "h-2.5 w-2.5",
    lg: "h-3 w-3",
  };

  // Get initials from name
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .substring(0, 2);
  };

  return (
    <div className="relative">
      <Avatar className={sizeClasses[size]}>
        <AvatarImage src={user.avatar} alt={user.name} />
        <AvatarFallback className="bg-planet-primary/20 text-planet-primary">
          {getInitials(user.name)}
        </AvatarFallback>
      </Avatar>

      {showStatus && (
        <span
          className={`absolute bottom-0 right-0 block rounded-full bg-green-500 ring-2 ring-white ${statusSizeClasses[size]}`}
        />
      )}
    </div>
  );
};

export default UserAvatar;
