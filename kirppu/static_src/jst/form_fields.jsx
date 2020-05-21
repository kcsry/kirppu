
export function Options({list, multiple}) {
    // multiple must be set here, otherwise the control will half-select first item by default.
    return (
        <select multiple={multiple} className="form-control">{
            list.map(t => {
                return <option value={t.name}>{t.description}</option>
            })
        }</select>
    )
}


export function PriceField({inputId, price_step, CURRENCY, readOnly}) {
    // If overridden, className must contain input-group
    return (
        <div className="input-group">
            {CURRENCY[0] && <span className="input-group-addon">{CURRENCY[0]}</span>}
            <input type="number" step={price_step} min="0" id={inputId} className="form-control" readOnly={readOnly}/>
            {CURRENCY[1] && <span className="input-group-addon">{CURRENCY[1]}</span>}
        </div>
    )
}
