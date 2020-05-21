
function Row({title, value, classes}) {
    return (
        <div className={"row " + (classes || "")}>
            <div className="col-xs-3 vendor-info-key">{title}</div>
            <div className="col-xs-9">{value}</div>
        </div>
    )
}

export default function render({text, vendor, title}) {
    return (
        <div className="vendor-info-box">
            {title && <h3>{gettext("Vendor")}</h3>}
            <Row title={text.name} value={vendor.name}/>
            <Row title={text.email} value={vendor.email} classes="hidden-print"/>
            <Row title={text.phone} value={vendor.phone} classes="hidden-print"/>
            <Row title={text.id} value={vendor.id}/>
            <Row title={text.terms_accepted_str} value={vendor.terms_accepted_str}/>
        </div>
    )
}
