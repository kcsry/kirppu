export default function render({value, min, max}) {
    max = max || 100
    return (
        <div className="progress">
            <div className="progress-bar"
                 role="progressbar"
                 aria-valuenow={value || 0} aria-valuemin={min || 0} aria-valuemax={max}
                 style={{width: (value || 0) * 100 / max + "%"}}
            >
            </div>
        </div>
    )
}
