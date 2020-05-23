export default function render({onConfirm, onAbort, onContinue, continueWarn, onRetry}) {
    const btns = [
        onConfirm &&
        <input type="button" className={"btn btn-success"}
               value={gettext('Confirm')}
               onclick={onConfirm}
        />

        , onAbort &&
        <input type="button" className="btn btn-default"
               value={gettext('Cancel')}
               onclick={onAbort}
        />

        , onRetry &&
        <input type="button" className="btn btn-primary"
               value={gettext('Retry')}
               onclick={onRetry}
        />

        , onContinue &&
        <input type="button" className={"btn " + (continueWarn ? "btn-warning" : "btn-primary")}
               value={gettext('Continue')}
               onclick={onContinue}
        />
    ]

    return (
        <div>
            {btns.reduce(
                (prev, cur) => {
                    if (cur) {
                        if (prev.length) prev.push(" ")
                        prev.push(cur)
                    }
                    return prev
                },
                []
            )}
        </div>
    )
}
