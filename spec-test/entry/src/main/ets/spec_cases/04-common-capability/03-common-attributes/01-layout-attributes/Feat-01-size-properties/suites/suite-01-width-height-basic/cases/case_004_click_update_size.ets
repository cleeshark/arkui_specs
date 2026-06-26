@Entry
@Component
export struct Case004ClickUpdateSize {
  @State widthVp: number = 100
  @State heightVp: number = 50

  build() {
    RelativeContainer() {
      Text('C004')
        .id('N_F01_C004_TARGET')
        .width(this.widthVp)
        .height(this.heightVp)
        .fontSize(16)
        .backgroundColor('#A0D8EF')
        .onClick(() => {
          this.widthVp = 160
          this.heightVp = 90
        })
        .alignRules({
          left: { anchor: '__container__', align: HorizontalAlign.Start },
          top: { anchor: '__container__', align: VerticalAlign.Top }
        })
    }
    .id('N_F01_C004_PARENT')
    .width(300)
    .height(300)
  }
}
