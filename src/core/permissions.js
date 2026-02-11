function hasRole(member, roleId) {
  if (!roleId) return false;
  return member.roles.cache.has(roleId);
}

function hasAnyRole(member, roleIds = []) {
  if (!Array.isArray(roleIds) || roleIds.length === 0) return false;
  return roleIds.some((roleId) => member.roles.cache.has(roleId));
}

module.exports = { hasRole, hasAnyRole };
