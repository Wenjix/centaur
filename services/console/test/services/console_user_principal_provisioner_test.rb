require "test_helper"

class ConsoleUserPrincipalProvisionerTest < ActiveSupport::TestCase
  test "creates and then reuses a scoped principal for the Console user" do
    user = users(:member_user)

    assert_difference -> { Principal.count }, 1 do
      @principal = ConsoleUserPrincipalProvisioner.call(user)
    end
    same_principal = ConsoleUserPrincipalProvisioner.call(user)

    assert_equal @principal, same_principal
    assert_equal "console_user", @principal.kind
    assert_equal user, @principal.console_user
    assert_equal "centaur", @principal.labels["managed-by"]
    assert_includes @principal.roles, Role.find_by!(foreign_id: "user-mcp")
  end

  test "repeated calls leave an unchanged principal untouched" do
    user = users(:member_user)
    principal = ConsoleUserPrincipalProvisioner.call(user)

    assert_no_changes -> { principal.reload.updated_at } do
      ConsoleUserPrincipalProvisioner.call(user)
    end
  end

  test "new console user principals receive the configured sandbox defaults" do
    SystemSetting.current.update!(
      default_sandbox_repo_cache: "none",
      default_sandbox_observability_enabled: false,
      default_sandbox_sessions_read_enabled: false,
      default_sandbox_workflows_read_enabled: false,
      default_sandbox_workflows_write_enabled: false
    )

    principal = ConsoleUserPrincipalProvisioner.call(users(:member_user))

    assert_equal "none", principal.sandbox_repo_cache
    assert_equal false, principal.sandbox_observability_enabled
    assert_equal false, principal.sandbox_sessions_read_enabled
    assert_equal false, principal.sandbox_workflows_read_enabled
    assert_equal false, principal.sandbox_workflows_write_enabled
  end

  test "administrator default changes do not rewrite existing principals" do
    principal = ConsoleUserPrincipalProvisioner.call(users(:member_user))
    assert_equal "all", principal.sandbox_repo_cache

    SystemSetting.current.update!(default_sandbox_repo_cache: "none")
    ConsoleUserPrincipalProvisioner.call(users(:member_user))

    assert_equal "all", principal.reload.sandbox_repo_cache
  end
end
