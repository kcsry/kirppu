export default function render({item, text}) {
    return (
        <dl className="dl-horizontal">
            <dt>{text.description}</dt>
            <dd>{item.description}</dd>

            <dt><span className="glyphicon glyphicon-warning-sign text-warning"/> {text.pricing}</dt>
            <dd>{text.bundle_size} / <span className="price">{item.item_price.formatCents()}</span></dd>

            <dt>{text.box_number}</dt>
            <dd>{item.box_number}</dd>
        </dl>
    )
}
