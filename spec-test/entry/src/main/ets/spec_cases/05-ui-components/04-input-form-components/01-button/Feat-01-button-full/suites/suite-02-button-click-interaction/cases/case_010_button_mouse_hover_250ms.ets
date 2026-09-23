@Entry
@Component
export struct Case010ButtonMouseHover250ms {
  @State markerWidth: number = 100

  build() {
    Column() {
      Button('Hover')
        .width(160)
        .height(48)
        .onHover((isHover: boolean) => {
          if (isHover) {
            this.markerWidth = 140
          }
        })
      Text('hovered')
        .id('N_BUTTON_US2_C010_TARGET')
        .width(this.markerWidth)
        .height(20)
    }
    .alignItems(HorizontalAlign.Start)
    .width(300)
    .height(200)
  }
}
