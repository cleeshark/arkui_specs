@Entry
@Component
export struct Case002WidthHeightBasic {
  build() {
    RelativeContainer() {
      Text('C002')
        .id('N_F01_C002_TARGET')
        .width(120)
        .height(80)
        .fontSize(16)
        .alignRules({
          left: { anchor: '__container__', align: HorizontalAlign.Start },
          top: { anchor: '__container__', align: VerticalAlign.Top }
        })
    }
    .id('N_F01_C002_PARENT')
    .width(300)
    .height(300)
  }
}
