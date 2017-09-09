# Base class for operation modes.
#
# @abstract
class @CheckoutMode

  # @param switcher [ModeSwitcher] ModeSwitcher to use.
  # @param config [Config, optional] Configuration instance override.
  constructor: (switcher, config) ->
    @switcher = switcher
    @cfg = if config then config else CheckoutConfig
    @_gatherCommands()

  # Gather values for commands-dictionary from subclass and base class.
  # This will replace the command-function with direct dictionary that is
  # joined from contents of both base class and subclass functions.
  _gatherCommands: ->
    # Join sub- and base class commands-objects.
    commandDescriptions = CheckoutMode.prototype.commands()
    for key, val of @commands()
      commandDescriptions[key] = val

    # Create key:command -dictionary.
    commands = {}
    for key, val of commandDescriptions
      commands[key] = val[0]
    @commands = commands
    @commandDescriptions = commandDescriptions

  # Glyph to display along the title.
  #
  # @return [String] Name of glyphicon without glyphicon- prefix.
  glyph: -> ""

  # Title to display in this mode.
  #
  # @return [String] Title string.
  title: -> "[unknown mode]"

  # Subtitle to display in this mode.
  #
  # @return [String, null] Subtitle string, if needed.
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"

  inputPlaceholder: -> gettext("Barcode")

  # Called after switching to this mode.
  enter: ->

  # Called after switching out of this mode.
  exit: ->

  # Return an dictionary of mode command prefixes and their "names" in Arrays.
  # Base class returns dictionary like {logout: [":exit", "Log out"]}. Then, after
  # base class constructor has been run, the prefixes can be accessed in
  # 'actions' -arrays like `@commands.logout`.
  #
  # @return [Object] Command prefixes with names.
  commands: ->
    # This is actually called by static reference.
    logout: ["exit", gettext("Log out")]

  # Return an Array where each element is a [prefix, handler function]
  # array. The handler will be called with (code, prefix) where code is
  # the input without the prefix.
  #
  # Would use an Object instead of an Array of Arrays if literal objects
  # with dynamic property names were supported.
  #
  # @return [Array] Mapping from prefixes to handler functions.
  actions: -> [["", ->]]

  onLogout: =>
    Api.clerk_logout().then(
      () =>
        @notifySuccess()
        console.log("Logged out #{ @cfg.settings.clerkName }.")
        @cfg.settings.clerkName = null
        @switcher.setOverseerVisible(false)
        @switcher.setStatsVisible(false)
        @switcher.switchTo(ClerkLoginMode)

      (jqXHR) =>
        safeAlert(gettext("Logout failed!") + " " + jqXHR.responseText)
        return true
    )

  notifySuccess: ->
    if UtilSound.success?
      UtilSound.success.play()
