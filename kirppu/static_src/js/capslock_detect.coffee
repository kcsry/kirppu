# Improvised from answers at
# http://stackoverflow.com/questions/348792/how-do-you-tell-if-caps-lock-is-on-using-javascript

lastCapsLockState = null

## Create Caps-lock activity detector event handler.
# Should be attached to an `input[type=text]` `keypress` event.
#
# @param callback [function] Called on caps-lock state change with boolean of the caps-lock state.
# @return [function] Event handler for keypress-event.
@capsLockDetect = (callback) ->
  return (event) ->
    event = event || window.event
    character = String.fromCharCode(event.keyCode || event.which)

    if character.toUpperCase() == character.toLowerCase()
      # Numeric, (backspace,) etc characters.
      return

    shift = if event.shiftKey then true else if event.modifiers then !!(event.modifiers & 4) else false

    # CapsLock is on, if pressing shift resulted lowercase letter,
    # or not pressing shift resulted uppercase letter.
    capsOn = shift and character.toLowerCase() == character or\
      !shift and character.toUpperCase() == character

    if not lastCapsLockState? or capsOn != lastCapsLockState
      lastCapsLockState = capsOn
      callback(capsOn)
