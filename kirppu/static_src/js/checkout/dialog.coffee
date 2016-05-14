# Dialog helper class for using BootStrap Modal Dialog with only one common template.
class @Dialog
  constructor: (template="#dialog_template", title="#dialog_template_label") ->
    @container = $(template)
    @title = @container.find(title)
    @body = @container.find(".modal-body")
    @buttons = @container.find(".modal-footer")

    @title.empty()
    @body.empty()
    @buttons.empty()

    @_buttonList = []
    @container.on("hidden.bs.modal", () =>
      @title.empty()
      @body.empty()
      @buttons.empty()
    )

  # Add positive button to the dialog.
  # @param clazz [optional] Initial btn-class to set to the button.
  # @return [$] Button object.
  addPositive: (clazz="success") ->
    return @addButton(clazz)

  # Add negative button to the dialog.
  # @param clazz [optional] Initial btn-class to set to the button.
  # @return [$] Button object.
  addNegative: (clazz="default") ->
    return @addButton(clazz)

  # Add a button to the dialog.
  # @params clazz Initial btn-class to set to the button.
  # @return [$] Button object.
  addButton: (clazz) ->
    btn = @_button(clazz)
    @_buttonList.push(btn)
    return btn

  # Enable or disable a button.
  # @param button [$] Button reference from `add*` functions.
  # @param enabled [Boolean, optional] Whether to enable (default) or disable the button.
  setEnabled: (button, enabled = true) ->
    if enabled
      button.removeAttr("disabled")
    else
      button.attr("disabled", "disabled")

  # Display the dialog. This will append added buttons to `buttons`-container.
  # @param modalArgs [optional] Arguments for BootStrap `modal()`.
  show: (modalArgs=keyboard:false) ->
    @buttons.append(@_buttonList)
    @container.modal(modalArgs)

  _button: (clazz="default") ->
    $("""<button type="button" class="btn btn-#{ clazz }" data-dismiss="modal">""")
