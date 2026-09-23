@Entry
@Component
export struct Case009ButtonTouchReleaseClick {
  @State downSeen: boolean = false
  @State upSeen: boolean = false
  @State clickSeen: boolean = false

  private updateMarkerWidth(): number {
    return this.downSeen && this.upSeen && this.clickSeen ? 160 : 100
  }

  build() {
    Column() {
      Button('Release')
        .width(160)
        .height(48)
        .onTouch((event: TouchEvent) => {
          if (event.type === TouchType.Down) {
            this.downSeen = true
          } else if (event.type === TouchType.Up) {
            this.upSeen = true
          }
        })
        .onClick(() => {
          this.clickSeen = true
        })
      Text('released')
        .id('N_BUTTON_US2_C009_TARGET')
        .width(this.updateMarkerWidth())
        .height(20)
    }
    .alignItems(HorizontalAlign.Start)
    .width(300)
    .height(200)
  }
}
