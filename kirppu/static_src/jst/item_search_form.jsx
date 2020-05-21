import {html} from './helpers';
import {Options, PriceField} from './form_fields.jsx';

export default function render({item_types, item_states, price_step, CURRENCY}) {
    return (
        <form role="form" className="form-horizontal">
            <div className="form-group">
                <label htmlFor="item_search_input" className="control-label col-sm-2">{gettext("Name / Bar code")}</label>
                <div className="input-group col-sm-10">
                    <input type="text" id="item_search_input" className="form-control"/>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item_code_search_input"
                       className="control-label col-sm-2">{gettext("Bar code part")}</label>
                <div className="input-group col-sm-10">
                    <input type="text" id="item_code_search_input" className="form-control"/>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="vendor_search_input" className="control-label col-sm-2">{gettext("Vendor ID")}</label>
                <div className="input-group col-sm-2">
                    <input type="number" step="1" min="1" id="vendor_search_input" className="form-control"/>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item_search_min_price"
                       className="control-label col-sm-2">{gettext("Minimum price")}</label>
                <PriceField inputId="item_search_min_price" className="input-group col-sm-2" price_step={price_step} CURRENCY={CURRENCY}/>
            </div>
            <div className="form-group">
                <label htmlFor="item_search_max_price"
                       className="control-label col-sm-2">{gettext("Maximum price")}</label>
                <PriceField inputId="item_search_max_price" className="input-group col-sm-2" price_step={price_step} CURRENCY={CURRENCY}/>
            </div>
            <div className="form-group">
                <label htmlFor="item_search_type" className="control-label col-sm-2">{gettext("Type")}</label>
                <div className="input-group col-sm-10">
                    <Options multiple id="item_search_type" list={item_types}/>
                    <span
                        className="help-block">{html(gettext("To select/deselect multiple values, press <kbd>Ctrl</kbd>, <kbd>Command</kbd> or <kbd>Shift</kbd> keys while clicking items."))}</span>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item_search_state" className="control-label col-sm-2">{gettext("State")}</label>
                <div className="input-group col-sm-10">
                    <Options multiple id="item_search_state" list={item_states}/>
                    <span
                        className="help-block">{html(gettext("To select/deselect multiple values, press <kbd>Ctrl</kbd>, <kbd>Command</kbd> or <kbd>Shift</kbd> keys while clicking items."))}</span>
                </div>
            </div>
            <div className="form-group">
                <div className="input-group col-sm-offset-2 col-sm-10">
                    <div className="checkbox">
                        <label>
                            <input type="checkbox" id="show_hidden_items"/>
                            {gettext("Show hidden items")}
                        </label>
                    </div>
                </div>
            </div>
            <div className="col-sm-offset-2">
                <button type="submit" className="btn btn-primary col-sm-1">{gettext("Search")}</button>
                <button type="reset" className="btn btn-default col-sm-1">{gettext("Reset")}</button>
            </div>
        </form>
    )
}
