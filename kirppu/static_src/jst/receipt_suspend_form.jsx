export default function render() {
    return (
        <form onSubmit="return false">
            <div className="form-group">
                <label htmlFor="suspend_note">{gettext("Note for suspend")}</label>
                <input type="text" className="form-control" id="suspend_note" placeholder="Text"/>
            </div>
        </form>
    )
}
