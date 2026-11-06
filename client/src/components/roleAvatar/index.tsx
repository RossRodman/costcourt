import { ROLES } from "@/constants";
import type { Role } from "@/types";
import { cn } from "@/utils/cn";

const SIZES = {
  sm: "size-6 rounded-md [&>svg]:size-3.5",
  md: "size-9 rounded-xl [&>svg]:size-4.5",
  lg: "size-11 rounded-xl [&>svg]:size-5",
} as const;

interface RoleAvatarProps {
  role: Role;
  size?: keyof typeof SIZES;
  className?: string;
}

export function RoleAvatar({ role, size = "md", className }: RoleAvatarProps) {
  const { icon: Icon, accent, title } = ROLES[role];
  return (
    <span
      title={title}
      className={cn(
        "inline-flex shrink-0 items-center justify-center ring-1",
        accent,
        SIZES[size],
        className,
      )}
    >
      <Icon aria-hidden />
    </span>
  );
}
