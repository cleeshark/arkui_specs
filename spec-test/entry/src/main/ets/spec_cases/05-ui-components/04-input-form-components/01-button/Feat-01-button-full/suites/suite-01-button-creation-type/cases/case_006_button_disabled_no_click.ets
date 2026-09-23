@Entry
@Component
export struct Case006ButtonDisabledNoClick {
  @State markerWidth: number = 100

  build() {
    Column() {
      Button('Disabled')
        .width(160)
        .height(48)
        .enabled(false)
        .onClick(() => {
          this.markerWidth = 160
        })
      Text('not-clicked')
        .id('N_BUTTON_US1_C006_TARGET')
        .width(this.markerWidth)
        .height(20)
    }
    .alignItems(HorizontalAlign.Start)
    .width(300)
    .height(200)
  }
}
