import { RoleAvatar } from "@/components/roleAvatar";
import { ROLE_ORDER, ROLES } from "@/constants";
import { Styled } from "@/styled";

export function HeroSection() {
  return (
    <header className="flex flex-col items-start gap-5">
      <p className={Styled.Eyebrow}>Put your estimate on trial</p>
      <h1 className={`max-w-3xl ${Styled.PageTitle}`}>
        Construction estimates, <span className="text-judge">argued out</span> before you sign.
      </h1>
      <p className={Styled.PageLead}>
        Three AI agents debate every line of your estimate. A judge weighs the arguments, rules on
        each disputed line and hands you a revised estimate with the full reasoning.
      </p>

      <ul aria-label="Debate roles" className="flex flex-wrap gap-2">
        {ROLE_ORDER.map((role) => (
          <li
            key={role}
            title={ROLES[role].blurb}
            className="flex items-center gap-2 rounded-full border border-line bg-surface py-1 pr-3 pl-1 text-sm"
          >
            <RoleAvatar role={role} size="sm" className="rounded-full" />
            {ROLES[role].title}
          </li>
        ))}
      </ul>
    </header>
  );
}
