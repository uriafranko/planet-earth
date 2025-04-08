
import { FileQuestion } from "lucide-react";
import { cn } from "@/lib/utils";

interface NoDataProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
}

const NoData: React.FC<NoDataProps> = ({
  title = "No data available",
  description = "There are no items to display at this time.",
  icon,
  className,
}) => {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center p-8 text-center",
      "border border-dashed rounded-md bg-muted/30",
      "min-h-[200px]",
      className
    )}>
      <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
        {icon || <FileQuestion className="h-8 w-8 text-muted-foreground" />}
      </div>
      <h3 className="text-lg font-medium text-foreground mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-md">{description}</p>
    </div>
  );
};

export default NoData;
