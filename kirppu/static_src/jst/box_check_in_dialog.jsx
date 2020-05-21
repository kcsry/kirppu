function fmtPricing(text, item) {
    if (item.box.bundle_size > 1) {
        return [
            <dt><span className="glyphicon glyphicon-warning-sign text-warning"/> {text.pricing}</dt>,
            <dd>{text.bundle_size} / <span className="price">{item.price.formatCents()}</span></dd>
        ]
    } else {
        return [
            <dt>{text.pricing}</dt>,
            <dd><span className="price">{item.price.formatCents()}</span></dd>
        ]
    }
}

export default function render({text, item}) {
    let defs = [
        <dt>{text.description}</dt>,
        <dd>{item.box.description}</dd>,

        <dt>{text.count}</dt>,
        <dd>{item.box.item_count}</dd>
    ]
    defs = defs.concat(fmtPricing(text, item))
    defs = defs.concat([
        <dt>{text.code}</dt>,
        <dd>{item.code}</dd>,

        <dt>{text.box_number}</dt>,
        <dd style="font-size: 170%">{item.box.box_number}</dd>
    ])
    return (
        <dl className="dl-horizontal">
            {defs}
        </dl>
    )
}
